from optimade.server.models.entries import EntryResourceAttributes, EntryResource
from optimade.server.models.util import conlist
from pydantic import Schema, BaseModel
from typing import List, Optional


class Species(BaseModel):
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


class Assembly(BaseModel):
    """ A container for sites that are statistically correlated.

* **Examples**:
  * `{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the
    first site and the second site never occur at the same time in the unit
    cell. Statistically, 30 % of the times the first site is present, while
    70 % of the times the second site is present.
  * `{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the
    second and third site are either present together or not present; they form
    the first group of atoms for this assembly. The second group is formed by
    the fourth site. Sites of the first group (the second and the third) are
    never present at the same time as the fourth site. 30 % of times sites 1 and
    2 are present (and site 3 is absent); 70 % of times site 3 is present
    (and sites 1 and 2 are absent).

"""

    sites_in_groups: List[int] = Schema(
        ...,
        description="""Index of the sites (0-based) that belong to each group
for each assembly.

* **Examples**:
  * `[[1], [2]]`: two groups, one with the second site, one with the third.
  * `[[1, 2], [3]]`: one group with the second and third site, one with the
    fourth.

""",
    )

    group_probabilities: List[float] = Schema(
        ...,
        description="""Statistical probability of each group. It MUST have the
same length as `sites_in_groups`. It SHOULD sum to one. The possible reasons for
the values not to sum to one are the same as those specified for the
`concentration` of each species inside `species`. """,
    )


class StructureResourceAttributes(EntryResourceAttributes):

    elements: List[str] = Schema(
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
a site potentially occupied by an atom, or a placeholder for a virtual mixture of
atoms (e.g., in a virtual crystal approximation).

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

    species: List[Species] = Schema(
        ...,
        description="""A list describing the species of the sites of this
structure. Species scan be pure chemical elements, or virtual-crystal atoms
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

    assemblies: Optional[List[Assembly]] = Schema(
        ...,
        description="""A description of groups of sites that are statistically
correlated.

* **Requirements/Conventions**:
  * If present, the correct flag MUST be set in the list `structure_features`.
  * Client implementations MUST check its presence (as its presence changes the
    interpretation of the structure).
  * If a site is not present in any group, it means that it is present with
    100 % probability (as if no assembly was specified).
  * A site MUST NOT appear in more than one group.

* **Notes**:
  * Assemblies are essential to represent, for instance, the situation where an
    atom can statistically occupy two different sites.
  * By defining groups, it is possible to represent, e.g., the case where a
    functional molecule (and not just one atom) is either present or absent (or
    the case where it is present in two conformations).
  * Considerations on virtual alloys and on vacancies:
    In the special case of a virtual alloy, these specifications allow two
    different, equivalent ways of specifying them. For instance, a site at the
    origin with 30 % probability of being occupied by Si, 50 % probability of
    being occupied by Ge, and 20 % of being a vacancy, the following two
    representations are possible:
    * Using a single species:
    ```
    {
      "cartesian_site_positions": [[0,0,0]],
      "species_at_sites": ["SiGe-vac"],
      "species": [
          {
            "name": "SiGe-vac",
            "chemical_symbols": ["Si", "Ge", "vacancy"],
            "concentration": [0.3, 0.5, 0.2]
          }
      ]
      // ...
    }
    ```
    * Using multiple species and the assemblies:
    ```
    {
      "cartesian_site_positions": [ [0,0,0], [0,0,0], [0,0,0] ],
      "species_at_sites": ["Si", "Ge", "vac"],
      "species": {
        "Si": { "chemical_symbols": ["Si"], "concentration": [1.0] },
        "Ge": { "chemical_symbols": ["Ge"], "concentration": [1.0] },
        "vac": { "chemical_symbols": ["vacancy"], "concentration": [1.0] }
      },
      "assemblies": [
        {
          "sites_in_groups": [ [0], [1], [2] ],
          "group_probabilities": [0.3, 0.5, 0.2]
        }
      ]
      // ...
    }
    ```
  * It is up to the database provider to decide which representation to use,
    typically depending on the internal format in which the structure is stored.
    However, given a structure identified by a unique ID, the API implementation
    MUST always provide the same representation for it.
  * The probabilities of occurrence of different assemblies are uncorrelated.
    So, for instance, in the following case with two assemblies:
    ```
    {
      "assemblies": [
        {
          "sites_in_groups": [ [0], [1] ],
          "group_probabilities": [0.2, 0.8],
        },
        {
          "sites_in_groups": [ [2], [3] ],
          "group_probabilities": [0.3, 0.7]
        }
      ]
    }
    ```

    Site 0 is present with a probability of 20 % and site 1 with a probability
    of 80 %. These two sites are correlated (either site 0 or 1 is present).
    Similarly, site 2 is present with a probability of 30 % and site 3 with a
    probability of 70 %. These two sites are correlated (either site 2 or 3 is
    present). However, the presence or absence of sites 0 and 1 is not
    correlated with the presence or absence of sites 2 and 3 (in the specific
    example, the pair of sites (0, 2) can occur with 0.2*0.3 = 6 % probability;
    the pair (0, 3) with 0.2*0.7 = 14 % probability; the pair (1, 2) with
    0.8*0.3 = 24 % probability; and the pair (1, 3) with 0.8*0.7 = 56 %
    probability).

""",
    )

    structure_features: List[str] = Schema(
        ...,
        description="""A list of strings, flagging which special features are
        used by the structure.

* **Requirements/Conventions**:
  * This property MUST be returned as an empty list if no special features are
    used.
  * This list MUST be sorted alphabetically.
  * If a special feature listed below is used, the corresponding string MUST be
    set.
  * If a special feature listed below is not used, the corresponding string MUST
  NOT be set.

* **List of special structure features**:
  * `disorder`: this flag MUST be present if any one entry in the `species` list
  has a `chemical_symbols` list longer than 1 element.
  * `unknown_positions`: this flag MUST be present if at least one component of
  the `cartesian_site_positions` list of lists has value `null`.
  * `assemblies`: this flag MUST be present if the `assemblies` list is present.

* **Querying**:
  * This property MUST be queryable.

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
