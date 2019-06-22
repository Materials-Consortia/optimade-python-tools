from optimade.server.models.entries import EntryResourceAttributes, EntryResource
from optimade.server.models.util import conlist
from pydantic import Schema, BaseModel
from typing import List, Optional


class Specie(BaseModel):
    """ A dictionary with the keys required to be used as a member of the
    `species` list.

    """

    name: str = Schema(
        ...,
        decsription="""The name of the species. MUST be a
unique value in the species list.""",
    )

    chemical_symbols: List[str] = Schema(
        ...,
        description="""MUST be a list of strings of all chemical elements
composing this species.

* It MUST be one of the following:
  * a valid chemical element name, or
  * the special value `"X"` to represent a non-chemical element, or
  * the special value `"vacancy"` to represent that this site has a non-zero
    probability of having a  vacancy (the respective probability is indicated in
    the `concentration` list.
* If any one entry in the `species` list has a `chemical_symbols` list longer
than 1 element, the correct flag MUST be set in the list `structure_features`.

""",
    )

    concentration: List[float] = Schema(
        ...,
        description="""MUST be a list of floats, with the same length as
`chemical_symbols`. The numbers represent the relative concentration of the
corresponding chemical symbol in this species. The numbers SHOULD sum to one.
Cases in which the numbers do not sum to one typically fall only in the
following two categories:
* Numerical errors when representing float numbers in fixed precision, e.g. for
two chemical symbols with concentrations `1/3` and `2/3` the concentration might
look something like `[0.33333333333, 0.66666666666]`. If the client is aware
that the sum is not one because of numerical precision, it can renormalize
values so that the sum is exactly one.
* Experimental error sin the data present in the database. In this case, it is
the responsibility of the client to decide how to process the data.

Note that concentrations are uncorrelated between different sites (even of the
same species).

""",
    )

    mass: Optional[float] = Schema(
        ..., description="If present, this MUST be a float expressed in a.m.u."
    )

    original_name: Optional[str] = Schema(
        ...,
        description="""Can be any valid Unicode string, and SHOULD contain (if
specified) the name of the species that is used internally in the source
database.

Note: With regards to "source database", we refer to the immediate source being
queried via the OPTiMaDe API implementation. The main use of this field is for
source databases that use species names, containing characters that are not
allowed (see description of the `species_at_sites` list).

""",
    )


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
    dimension_types: conlist(len_eq=3) = Schema(
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

    lattice_types: Optional[List[conlist(len_eq=3)]] = Schema(
        ...,
        description="""List of three lattice vectors in Cartesian coordinates,
in ångströms (Å).

* **Requirements/Conventions**:
  * This property is REQUIRED, except when `dimension_types` is equal to
    `[0, 0, 0]` (in which case it is optional).
  * It MUST be a list of three vectors *a*, *b* and *c*, where each of the
    vectors MUST BE a list of the vector's coordinates along the x, y and z
    Cartesian coordinates. (Therefore, the first index runs over the three
    lattice vectors and the second index runs over the x, y, z Cartesian
    coordinates.)
  * For databases that do not define an absolute Cartesian system (e.g. only
    defining the length and angles between vectors), the first lattice vector
    SHOULD be set along x and the second on the xy plane.
  * This property MUST be an array of dimensions 3 times 3 regardless of the
    elements of `dimension_types`. The vectors SHOULD by convention be chosen
    so the determinant of the `lattice_vectors` matrix is different from zero.
    The vectors in the non-periodic directions have no significance beyond
    fulfilling these requirements.

* **Examples**:
  * `[[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 1.0, 4.0]]` represents a cell,
    where the first vector is (4, 0, 0), i.e., a vector aligned along the x axis
    of length 4 Å; the second vector is (0, 4, 0); and the third vector is
    (0, 1, 4).

""",
    )

    cartesian_site_positions: List[conlist(len_eq=3)] = Schema(
        ...,
        description="""The Cartesian positions of each site. A site is an atom,
a site potentiall occupied by an atom, or a placeholder for a virtual mixture of
atoms (e.g., in a virutal crystal approximation).

* **Requirements/Conventions**:
  * It MUST be a list of length N times 3, where N is the number of sites in the
    structure.
  * An entry MAY have multiple sites at the same Cartesian position (for a
    relevant use of this, see e.g., the `assemblies` property.

* **Examples**:
  * `[[0, 0, 0], [0, 0, 2]]` indicates a structure with two sites, one sitting
    at the origin and one along the (positive) z axis, 2 Å away from the origin.

""",
    )

    nsites: int = Schema(
        ...,
        description="""An integer specifying the length of the
`cartesian_site_positions` property.

* **Requirements/Conventions**:
  * Queries on this property can be equivalently formulated using
`LENGTH cartesian_site_positions`.

""",
    )

    species_at_sites: List[str] = Schema(
        ...,
        description="""Name of the species at each site (where values for sites
are specified with the same order of the `cartesian_site_positions` property).
The properties of the species are found in the `species` property.

* **Requirements/Conventions**:
  * It MUST be a list of strings, which MUST have length equal to the number of
    sites in the structure (the first dimension of the
    `cartesian_site_positions` list.
  * Each species MUST have a unique name.
  * Each species name mentioned in the `species_at_sites` list MUST be described
    in the `species` list (i.e. for each value in the `species_at_sites` list
    there MUST exist exactly one dictionary in the `species` list with the
    `name` attribute equal to the corresponding `species_at_sites` value).
  * Each site MUST be associated only to a single species. However, species can
    represent mixtures of atoms, and multiple species MAY be defined for the
    same chemical element. This latter case is useful when different atoms of
    the same type need to be grouped or distinguished, for instance in
    simulation codes to assign different initial spin states.

* **Examples**:
  * `["Ti", "O2"]` indicates that the first site is hosting a species labelled
  `"Ti"` and the second a species labelled `"O2"`.

  """,
    )

    species: List[Specie] = Schema(
        ...,
        description="""A list describing the species of the sites of this
structure. Specie scan be pure chemical elements, or virtual-crystal atoms
representing a statistical occupation of a given site by multiple chemical
elements.

* **Requirements/Conventions**:
  * Systems that have only species formed by a single chemical symbol, and
    that have at most one species per chemical symbol, SHOULD use the chemical
    symbol as species name (e.g., "Ti" for titanium, "O" for oxygen, etc.)
    However, note that this is OPTIONAL, and client implementations MUST NOT
    assume that the key corresponds to a chemical symbol, nor assume that if the
    species name is a valid chemical symbol, that it represents a species with
    that chemical symbol. This means that a species
    `{"name": "C", "chemical_symbols": ["Ti"], "concentration": [0.0]}` is valid
    and represents a titanium species (and *not* a carbon species).
  * It is NOT RECOMMENDED that a structure includes species that do not have at
    least one corresponding site.

* **Examples**:
  * `"species": [ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration":
    [1.0]}, ]`: any site with this species is occupied by a Ti atom.
  * `"species": [ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"],
    "concentration": [0.9, 0.1]}, ]`: any site with this species is occupied by
    a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
  * `"species": [ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"],
    "concentration": [0.05, 0.45, 0.5], "mass": 88.5}, ]`: any site with this
    species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 %
    probability, and by a vacancy with 5 % probability. The mass of this site is
    (on average) 88.5 a.m.u.
  * `"species": [ {"name": "C12", "chemical_symbols": ["C"], "concentration":
    [1.0], "mass": 12.0}, ]`: any site with this species is occupied by a carbon
    isotope with mass 12.
  * `"species": [ {"name": "C13", "chemical_symbols": ["C"], "concentration":
    [1.0], "mass": 13.0}, ]`: any site with this species is occupied by a carbon
    isotope with mass 13.

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
