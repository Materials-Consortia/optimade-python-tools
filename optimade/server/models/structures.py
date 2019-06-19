from optimade.server.models.entries import EntryResourceAttributes, EntryResource
from optimade.server.models.util import ConstrainedList, conlist
from pydantic import Schema, constr, errors
from typing import List, Optional, Any


class StructureResourceAttributes(EntryResourceAttributes):

    elements: str = Schema(
        ...,
        description="""Names of elements found in the structure as a list of strings,
in alphabetical order.
""",
    )

    nelements: int = Schema(..., description="Number of elements found in a structure.")

    elements_ratios: List[float] = Schema(
        ...,
        description="""Relative proportions of different elements in the structure.
This must sum to 1.0 (within floating point accuracy).
""",
    )

    chemical_formula_descriptive: str = Schema(
        ...,
        description="""The chemical formula for a structure as a string in a form
chosen by the API implementation.

* **Requirements/Conventions**:
  * The chemical formula is given as a string consisting of properly capitalized
    element symbols followed by integers or decimal numbers, balanced parentheses,
    square, and curly brackets `(`, `)`, `[`, `]`, `{`, `}`, commas, the `+`, `-`,
    `:` and `=` symbols. The parentheses are allowed to be followed by a number.
    Spaces are allowed anywhere except within chemical symbols. The order of elements
    and any groupings indicated by parentheses or brackets are chosen freely by the
    API implementation.
  * The string SHOULD be arithmetically consistent with the element ratios in the
    `chemical_formula_reduced` property.
  * It is RECOMMENDED, but not mandatory, that symbols, parentheses and brackets, if
    used, are used with the meanings prescribed by IUPAC's Nomenclature of Organic
    Chemistry.

* **Examples**:
  * `"(H2O)2 Na"`
  * `"NaCl"`
  * `"CaCO3"`
  * `"CCaO3"`
  * `"(CH3)3N+ - [CH2]2-OH = Me3N+ - CH2 - CH2OH"`

""",
    )

    chemical_formula_reduced: str = Schema(
        ...,
        description="""The reduced chemical formula for a structure as a string with
element symbols and integer chemical proportion numbers.

* **Requirements/Conventions**:
  * Element names MUST have proper capitalization (e.g. "Si", not "SI" for "silicon").
  * Elements MUST be placed in alphabetical order, followed by their integer chemical
    proportion number.
  * For structures with no partial occupation, the chemical proportion numbers are the
    smallest integers for which the chemical proportion is exactly correct.
  * For structures with partial occupation, the chemical proportion numbers are integers
    that within reasonable approximation indicate the correct chemical proportions. The
    precise details of how to perform the rounding is chosen by the API implementation.
  * No spaces or separators are allowed.
  * Support for filters using partial string matching with this property is OPTIONAL
    (i.e., BEGINS WITH, ENDS WITH, and CONTAINS). Intricate querying on formula
    components are instead recommended to be formulated using set-type filter operators
    on the multi valued `elements` and `elements_proportions` properties.

* **Examples**:
  * `"H2NaO"`
  * `"ClNa"`
  * `"CCaO3"`

""",
    )

    chemical_formula_hill: Optional[str] = Schema(
        ...,
        description="""The chemical formula for a structure as a string in
[Hill form](https://dx.doi.org/10.1021/ja02046a005) with element symbols followed by
integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.

* **Requirements/Conventions**:
  * The overall scale factor of the chemical proportions is chosen such that the
    resulting values are integers that indicate the most chemically relevant unit of
    which the system is composed. For example, if the structure is a repeating unit cell
    with four hydrogens and four oxygens that represents two hydroperoxide molecules,
    `chemical_formula_hill` is `H2O2` (i.e., not `HO`, nor `H4O4`).
  * If the chemical insight needed to ascribe a Hill formula to the system is not
    present, the property MUST be handled as unset.
  * Element names MUST have proper capitalization (e.g. "Si", not "SI" for "silicon").
  * Elements MUST be placed in [Hill order](https://dx.doi.org/10.1021/ja02046a005),
    followed by their integer chemical proportion number. Hill order means: if carbon
    is present, it is placed first, and if also present, hydrogen is placed second.
    After that, all other elements are ordered alphabetically. If carbon is not present,
    all elements are ordered alphabetically.
  * If the system has sites with partial occupation and the total occupations of each
    element do not all sum up to integers, then the Hill formula SHOULD be handled as
    unset.
  * No spaces or separators are allowed.

* **Examples**:
  * `"H2O2"`

""",
    )

    chemical_formula_anonymous: str = Schema(
        ...,
        description="""The anonymous formula is the `chemical_formula_reduced`, but
where the elements are instead first ordered by their chemical proportion number, and
then, in order left to right, replaced by anonymous symbols
`A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ...` and so on.

* **Requirements/Conventions**:
  * Support for filters using partial string matching with this property is OPTIONAL
    (i.e. BEGINS WITH, ENDS WITH and CONTAINS).

* **Examples**:
  * `"A2B"`
  * `"A42B42C16D12E10F9G5"`

""",
    )

    # FIXME: re-enable this when we have length constraint working
    dimension_types: ConstrainedList[int, conlis:(len_eq=3)] = Schema(
        # dimension_types: List[int] = Schema(
        ...,
        description="""List of three integers. For each of the three directions
indicated by the three lattice vectors (see property `lattice_vectors`). This list
indicates if the direction is periodic (value `1`) or non-periodic (value `0`). Note:
the elements in this list each refer to the direction of the corresponding entry in
`lattice_vectors`.

* **Requirements/Conventions**:
  * Each element MUST be an integer and MUST assume only the value of `0` or `1`.

* **Examples**:
  * For a molecule: `[0, 0, 0]`
  * For a wire along the direction specified by the third lattice vector: `[0, 0, 1]`.
  * For a 2D surface/slab, periodic on the plane defined by the first and third lattice
    vectors: `[1, 0, 1]`.
  * For a bulk 3D system: `[1, 1, 1]`.

""",
    )


class StructureResource(EntryResource):
    """Representing a structure."""

    type = "structure"
    attributes: StructureResourceAttributes


class StructureMapper:
    aliases = (
        ("id", "task_id"),
        ("local_id", "task_id"),
        ("last_modified", "last_updated"),
        ("formula_prototype", "formula_anonymous"),
        ("chemical_formula", "pretty_formula"),
    )

    list_fields = ("elements",)

    @classmethod
    def alias_for(cls, field):
        return dict(cls.aliases).get(field, field)

    @classmethod
    def map_back(cls, doc):
        if "_id" in doc:
            del doc["_id"]
        print(doc)
        mapping = ((real, alias) for alias, real in cls.aliases)
        newdoc = {}
        reals = {real for alias, real in cls.aliases}
        for k in doc:
            if k not in reals:
                newdoc[k] = doc[k]
        for real, alias in mapping:
            if real in doc:
                newdoc[alias] = doc[real]
        for k in newdoc:
            if k in cls.list_fields:
                newdoc[k] = ",".join(sorted(newdoc[k]))

        print(newdoc)
        if "attributes" in newdoc:
            raise Exception("Will overwrite doc field!")
        newdoc["attributes"] = newdoc.copy()
        newdoc["attributes"].pop("id")
        for k in list(newdoc.keys()):
            if k not in ("id", "attributes"):
                del newdoc[k]
        return newdoc
