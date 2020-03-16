# pylint: disable=no-self-argument,line-too-long,no-name-in-module
from enum import IntEnum
from sys import float_info
from typing import List, Optional, Tuple, Union

from pydantic import Field, BaseModel, validator

from .entries import EntryResourceAttributes, EntryResource
from .utils import CHEMICAL_SYMBOLS, EXTRA_SYMBOLS


EXTENDED_CHEMICAL_SYMBOLS = CHEMICAL_SYMBOLS + EXTRA_SYMBOLS


__all__ = ("Species", "Assembly", "StructureResourceAttributes", "StructureResource")


EPS = float_info.epsilon


Vector3D = Tuple[Union[float, None], Union[float, None], Union[float, None]]


class Periodicity(IntEnum):
    APERIODIC = 0
    PERIODIC = 1


class Species(BaseModel):
    """A list describing the species of the sites of this structure.
    Species can be pure chemical elements, or virtual-crystal atoms representing a statistical occupation of a given site by multiple chemical elements.

    - **Examples**:

        - :val:`[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]`: any site with this species is occupied by a Ti atom.
        - :val:`[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]`: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
        - :val:`[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": 88.5} ]`: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability. The mass of this site is (on average) 88.5 a.m.u.
        - :val:`[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": 12.0} ]`: any site with this species is occupied by a carbon isotope with mass 12.
        - :val:`[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": 13.0} ]`: any site with this species is occupied by a carbon isotope with mass 13.

    """

    name: str = Field(
        ...,
        decsription="""REQUIRED; gives the name of the species; the **name** value MUST be unique in the :property:`species` list;""",
    )

    chemical_symbols: List[str] = Field(
        ...,
        description="""MUST be a list of strings of all chemical elements composing this species.

- It MUST be one of the following:

  - a valid chemical-element name, or
  - the special value :val:`"X"` to represent a non-chemical element, or
  - the special value :val:`"vacancy"` to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the :property:`concentration` list, see below).

-  If any one entry in the :property:`species` list has a :property:`chemical_symbols` list that is longer than 1 element, the correct flag MUST be set in the list :property:`structure_features` (see property `structure_features`_).""",
    )

    concentration: List[float] = Field(
        ...,
        description="""MUST be a list of floats, with same length as :property:`chemical_symbols`. The numbers represent the relative concentration of the corresponding chemical symbol in this species.
The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

  - Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations :val:`1/3` and :val:`2/3`, the concentration might look something like :val:`[0.33333333333, 0.66666666666]`. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
  - Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

Note that concentrations are uncorrelated between different site (even of the same species).""",
    )

    mass: Optional[float] = Field(
        None,
        description="""If present MUST be a float expressed in a.m.u.""",
        unit="a.m.u.",
    )

    original_name: Optional[str] = Field(
        None,
        description="""Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation.
The main use of this field is for source databases that use species names, containing characters that are not allowed (see description of the list property `species_at_sites`_).""",
    )

    @validator("chemical_symbols", each_item=True)
    def validate_chemical_symbols(cls, v):
        if not (v in EXTENDED_CHEMICAL_SYMBOLS):
            raise ValueError(f"{v} MUST be in {EXTENDED_CHEMICAL_SYMBOLS}")
        return v

    @validator("concentration")
    def validate_concentration(cls, v, values):
        if len(v) != len(values.get("chemical_symbols", [])):
            raise ValueError(
                f"Length of concentration ({len(v)}) MUST equal length of chemical_symbols ({len(values.get('chemical_symbols', 'Not specified'))})"
            )
        return v


class Assembly(BaseModel):
    """A description of groups of sites that are statistically correlated.

    - **Examples** (for each entry of the assemblies list):

        - :val:`{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the first site and the second site never occur at the same time in the unit cell.
            Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.
        - :val:`{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the second and third site are either present together or not present; they form the first group of atoms for this assembly.
            The second group is formed by the fourth site.
            Sites of the first group (the second and the third) are never present at the same time as the fourth site.
            30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

    """

    sites_in_groups: List[List[int]] = Field(
        ...,
        description="""Index of the sites (0-based) that belong to each group for each assembly.

Example: :val:`[[1], [2]]`: two groups, one with the second site, one with the third.
Example: :val:`[[1,2], [3]]`: one group with the second and third site, one with the fourth.""",
    )

    group_probabilities: List[float] = Field(
        ...,
        description="""Statistical probability of each group. It MUST have the same length as :property:`sites_in_groups`.
It SHOULD sum to one.
See below for examples of how to specify the probability of the occurrence of a vacancy.
The possible reasons for the values not to sum to one are the same as already specified above for the :property:`concentration` of each :property:`species`, see property `species`_.""",
    )

    @validator("sites_in_groups")
    def validate_sites_in_groups(cls, v):
        sites = []
        for group in v:
            sites.extend(group)
        if len(set(sites)) != len(sites):
            raise ValueError(
                f"A site MUST NOT appear in more than one group. Given value: {v}"
            )
        return v

    @validator("group_probabilities")
    def check_self_consistency(cls, v, values):
        if len(v) != len(values.get("sites_in_groups", [])):
            raise ValueError(
                f"sites_in_groups and group_probabilities MUST be of same length, but are {len(values.get('sites_in_groups', 'Not specified'))} and {len(v)}, respectively"
            )
        return v


class StructureResourceAttributes(EntryResourceAttributes):
    """This class contains the Field for the attributes used to represent a structure, e.g. unit cell, atoms, positions."""

    elements: List[str] = Field(
        ...,
        description="""Names of the different elements present in the structure.
- **Type**: list of strings.
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.
  - The strings are the chemical symbols, written as uppercase letter plus optional lowercase letters.
  - The order MUST be alphabetical.
  - Note: This may not contain the "x" that is suggested in chemical_symbols for the :property:`species` property.

- **Examples**:

  - :val:`["Si"]`
  - :val:`["Al","O","Si"]`

- **Query examples**:
  - A filter that matches all records of structures that contain Si, Al **and** O, and possibly other elements: :filter:`elements HAS ALL "Si", "Al", "O"`.
  - To match structures with exactly these three elements, use :filter:`elements HAS ALL "Si", "Al", "O" AND LENGTH elements = 3`.""",
    )

    nelements: int = Field(
        ...,
        description="""Number of different elements in the structure as an integer.
- **Type**: integer
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.

- **Example**: :val:`3`
- **Querying**:

  -  Note: queries on this property can equivalently be formulated using :filter-fragment:`LENGTH elements`.
  -  A filter that matches structures that have exactly 4 elements: :filter:`nelements=4`.
  -  A filter that matches structures that have between 2 and 7 elements: :filter:`nelements>=2 AND nelements<=7`.""",
    )

    elements_ratios: List[float] = Field(
        ...,
        description="""Relative proportions of different elements in the structure.
- **Type**: list of floats
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.
  - Composed by the proportions of elements in the structure as a list of floating point numbers.
  - The sum of the numbers MUST be 1.0 (within floating point accuracy)

- **Examples**:

  - :val:`[1.0]`
  - :val:`[0.3333333333333333, 0.2222222222222222, 0.4444444444444444]`

- **Query examples**:

  - Note: useful filters can be formulated using the set operator syntax for correlated values. However, since the values are floating point values, the use of equality comparisons is generally not recommended.
  - A filter that matches structures where approximately 1/3 of the atoms in the structure are the element Al is: :filter:`elements:elements_ratios HAS ALL "Al":>0.3333, "Al":<0.3334`.""",
    )

    chemical_formula_descriptive: str = Field(
        ...,
        description="""The chemical formula for a structure as a string in a form chosen by the API implementation.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.
  - The chemical formula is given as a string consisting of properly capitalized element symbols followed by integers or decimal numbers, balanced parentheses, square, and curly brackets ``(``, ``)``, ``[``, ``]``, ``{``, ``}``, commas, the ``+``, ``-``, ``:`` and ``=`` symbols.
    The parentheses are allowed to be followed by a number.
    Spaces are allowed anywhere except within chemical symbols.
    The order of elements and any groupings indicated by parentheses or brackets are chosen freely by the API implementation.
  - The string SHOULD be arithmetically consistent with the element ratios in the :property:`chemical_formula_reduced` property.
  - It is RECOMMENDED, but not mandatory, that symbols, parentheses and brackets, if used, are used with the meanings prescribed by `IUPAC's Nomenclature of Organic Chemistry <https://www.qmul.ac.uk/sbcs/iupac/bibliog/blue.html>`__.

- **Examples**:

  - :val:`"(H2O)2 Na"`
  - :val:`"NaCl"`
  - :val:`"CaCO3"`
  - :val:`"CCaO3"`
  - :val:`"(CH3)3N+ - [CH2]2-OH = Me3N+ - CH2 - CH2OH"`

- **Query examples**:

  - Note: the free-form nature of this property is likely to make queries on it across different databases inconsistent.
  - A filter that matches an exactly given formula: :filter:`chemical_formula_descriptive="(H2O)2 Na"`.
  - A filter that does a partial match: :filter:`chemical_formula_descriptive CONTAINS "H2O"`.""",
    )

    chemical_formula_reduced: str = Field(
        ...,
        description="""The reduced chemical formula for a structure as a string with element symbols and integer chemical proportion numbers.
  The proportion number MUST be omitted if it is 1.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property.
    However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).
    Intricate querying on formula components are instead recommended to be formulated using set-type filter operators on the multi valued :property:`elements` and :property:`elements_proportions` properties.
  - Element names MUST have proper capitalization (e.g., :val:`"Si"`, not :VAL:`"SI"` for "silicon").
  - Elements MUST be placed in alphabetical order, followed by their integer chemical proportion number.
  - For structures with no partial occupation, the chemical proportion numbers are the smallest integers for which the chemical proportion is exactly correct.
  - For structures with partial occupation, the chemical proportion numbers are integers that within reasonable approximation indicate the correct chemical proportions. The precise details of how to perform the rounding is chosen by the API implementation.
  - No spaces or separators are allowed.

- **Examples**:

  - :val:`"H2NaO"`
  - :val:`"ClNa"`
  - :val:`"CCaO3"`

- **Query examples**:

  - A filter that matches an exactly given formula is :filter:`chemical_formula_reduced="H2NaO"`.""",
    )

    chemical_formula_hill: Optional[str] = Field(
        None,
        description="""The chemical formula for a structure in `Hill form <https://dx.doi.org/10.1021/ja02046a005>`__ with element symbols followed by integer chemical proportion numbers.
  The proportion number MUST be omitted if it is 1.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: OPTIONAL, i.e., MAY be :val:`null`.
  - **Query**: Support for queries on these properties are OPTIONAL. If supported, only a subset of filter operators MAY be supported.
  - The overall scale factor of the chemical proportions is chosen such that the resulting values are integers that indicate the most chemically relevant unit of which the system is composed.
    For example, if the structure is a repeating unit cell with four hydrogens and four oxygens that represents two hydroperoxide molecules, :property:`chemical_formula_hill` is :val:`"H2O2"` (i.e., not :val:`"HO"`, nor :val:`"H4O4"`).
  - If the chemical insight needed to ascribe a Hill formula to the system is not present, the property MUST be handled as unset.
  - Element names MUST have proper capitalization (e.g., :val:`"Si"`, not :VAL:`"SI"` for "silicon").
  - Elements MUST be placed in `Hill order <https://dx.doi.org/10.1021/ja02046a005>`__, followed by their integer chemical proportion number.
    Hill order means: if carbon is present, it is placed first, and if also present, hydrogen is placed second.
    After that, all other elements are ordered alphabetically.
    If carbon is not present, all elements are ordered alphabetically.
  - If the system has sites with partial occupation and the total occupations of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.
  - No spaces or separators are allowed.

- **Examples**:
  - :val:`"H2O2"`

- **Query examples**:

  - A filter that matches an exactly given formula is :filter:`chemical_formula_hill="H2O2"`.""",
    )

    chemical_formula_anonymous: str = Field(
        ...,
        description="""The anonymous formula is the :property:`chemical_formula_reduced`, but where the elements are instead first ordered by their chemical proportion number, and then, in order left to right, replaced by anonymous symbols A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property. However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).

- **Examples**:

  - :val:`"A2B"`
  - :val:`"A42B42C16D12E10F9G5"`

- **Querying**:
  - A filter that matches an exactly given formula is :filter:`chemical_formula_anonymous="A2B"`.""",
    )

    dimension_types: Tuple[Periodicity, Periodicity, Periodicity] = Field(
        ...,
        description="""List of three integers.
  For each of the three directions indicated by the three lattice vectors (see property `lattice_vectors`_).
  This list indicates if the direction is periodic (value :val:`1`) or non-periodic (value :val:`0`).
  Note: the elements in this list each refer to the direction of the corresponding entry in property `lattice_vectors`_ and *not* the Cartesian x, y, z directions.
- **Type**: list of integers.
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property. Support for equality comparison is REQUIRED, support for other comparison operators are OPTIONAL.
  - MUST be a list of length 3.
  - Each integer element MUST assume only the value 0 or 1.

- **Examples**:

  - For a molecule: :val:`[0, 0, 0]`
  - For a wire along the direction specified by the third lattice vector: :val:`[0, 0, 1]`
  - For a 2D surface/slab, periodic on the plane defined by the first and third lattice vectors: :val:`[1, 0, 1]`
  - For a bulk 3D system: :val:`[1, 1, 1]`""",
    )

    lattice_vectors: Optional[Tuple[Vector3D, Vector3D, Vector3D]] = Field(
        None,
        description="""The three lattice vectors in Cartesian coordinates, in ångström (Å).
- **Type**: list of list of floats.
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators.
  - MUST be a list of three vectors *a*, *b*, and *c*, where each of the vectors MUST BE a list of the vector's coordinates along the x, y, and z Cartesian coordinates.
    (Therefore, the first index runs over the three lattice vectors and the second index runs over the x, y, z Cartesian coordinates).
  - For databases that do not define an absolute Cartesian system (e.g., only defining the length and angles between vectors), the first lattice vector SHOULD be set along *x* and the second on the *xy*-plane.
  - This property MUST be an array of dimensions 3 times 3 regardless of the elements of :property:`dimension_types`.
    The vectors SHOULD by convention be chosen so the determinant of the :property:`lattice_vectors` matrix is different from zero.
    The vectors in the non-periodic directions have no significance beyond fulfilling these requirements.
  - All three elements of the inner lists of floats MAY be :val:`null` for non-periodic dimensions, i.e., those dimensions for which :property:`dimension_types` is :val:`0`.

- **Examples**:

  - :val:`[[4.0,0.0,0.0],[0.0,4.0,0.0],[0.0,1.0,4.0]]` represents a cell, where the first vector is :val:`(4, 0, 0)`, i.e., a vector aligned along the :val:`x` axis of length 4 Å; the second vector is :val:`(0, 4, 0)`; and the third vector is :val:`(0, 1, 4)`.""",
        unit="Å",
    )

    cartesian_site_positions: List[Vector3D] = Field(
        ...,
        description="""Cartesian positions of each site. A site is an atom, a site potentially occupied by an atom, or a placeholder for a virtual mixture of atoms (e.g., in a virtual crystal approximation).
- **Type**: list of list of floats and/or unknown values
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.
  - It MUST be a list of length N times 3, where N is the number of sites in the structure.
  - An entry MAY have multiple sites at the same Cartesian position (for a relevant use of this, see e.g., the property `assemblies`_).
  - If a component of the position is unknown, the :val:`null` value should be provided instead (see section `Properties with unknown value`_).
    Otherwise, it should be a float value, expressed in angstrom (Å).
    If at least one of the coordinates is unknown, the correct flag in the list property `structure_features`_ MUST be set.
  - **Notes**: (for implementers) While this is unrelated to this OPTIMADE specification: If you decide to store internally the :property: `cartesian_site_positions` as a float array, you might want to represent :val:`null` values with :field-val:`NaN` values.
    The latter being valid float numbers in the IEEE 754 standard in `IEEE 754-1985 <https://doi.org/10.1109/IEEESTD.1985.82928>`__ and in the updated version `IEEE 754-2008 <https://doi.org/10.1109/IEEESTD.2008.4610935>`__.

- **Examples**:

  - :val:`[[0,0,0],[0,0,2]]` indicates a structure with two sites, one sitting at the origin and one along the (positive) *z*-axis, 2 Å away from the origin.""",
        unit="Å",
    )

    nsites: int = Field(
        ...,
        description="""An integer specifying the length of the :property:`cartesian_site_positions` property.
- **Type**: integer
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.

- **Examples**:

  - :val:`42`

- **Query examples**:

  - Match only structures with exactly 4 sites: :filter:`nsites=4`
  - Match structures that have between 2 and 7 sites: :filter:`nsites>=2 AND nsites<=7`""",
    )

    species_at_sites: List[str] = Field(
        ...,
        description="""Name of the species at each site (where values for sites are specified with the same order of the property `cartesian_site_positions`_).
  The properties of the species are found in the property `species`_.
- **Type**: list of strings.
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.
  - MUST have length equal to the number of sites in the structure (first dimension of the list property `cartesian_site_positions`_).
  - Each species MUST have a unique name.
  - Each species name mentioned in the :property:`species_at_sites` list MUST be described in the list property `species`_ (i.e. for each value in the :property:`species_at_sites` list there MUST exist exactly one dictionary in the :property:`species` list with the :property:`name` attribute equal to the corresponding :property:`species_at_sites` value).
  - Each site MUST be associated only to a single species.
    **Note**: However, species can represent mixtures of atoms, and multiple species MAY be defined for the same chemical element.
    This latter case is useful when different atoms of the same type need to be grouped or distinguished, for instance in simulation codes to assign different initial spin states.

- **Examples**:

  - :val:`["Ti","O2"]` indicates that the first site is hosting a species labeled :val:`"Ti"` and the second a species labeled :val:`"O2"`.""",
    )

    species: List[Species] = Field(
        ...,
        description="""A list describing the species of the sites of this structure. Species can be pure chemical elements, or virtual-crystal atoms representing a statistical occupation of a given site by multiple chemical elements.
- **Type**: list of dictionary with keys:

  - :property:`name`: string (REQUIRED)
  - :property:`chemical_symbols`: list of strings (REQUIRED)
  - :property:`concentration`: list of float (REQUIRED)
  - :property:`mass`: float (OPTIONAL)
  - :property:`original_name`: string (OPTIONAL).

- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators.
  - Each list member MUST be a dictionary with the following keys:

    - **name**: REQUIRED; gives the name of the species; the **name** value MUST be unique in the :property:`species` list;

    - **chemical_symbols**: REQUIRED; MUST be a list of strings of all chemical elements composing this species.

      - It MUST be one of the following:

        - a valid chemical-element name, or
        - the special value :val:`"X"` to represent a non-chemical element, or
        - the special value :val:`"vacancy"` to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the :property:`concentration` list, see below).

      -  If any one entry in the :property:`species` list has a :property:`chemical_symbols` list that is longer than 1 element, the correct flag MUST be set in the list :property:`structure_features` (see property `structure_features`_).

    - **concentration**: REQUIRED; MUST be a list of floats, with same length as :property:`chemical_symbols`. The numbers represent the relative concentration of the corresponding chemical symbol in this species.
      The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

      - Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations :val:`1/3` and :val:`2/3`, the concentration might look something like :val:`[0.33333333333, 0.66666666666]`. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
      - Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

      Note that concentrations are uncorrelated between different site (even of the same species).

    - **mass**: OPTIONAL. If present MUST be a float expressed in a.m.u.
    - **original_name**: OPTIONAL. Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

        Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation.
            The main use of this field is for source databases that use species names, containing characters that are not allowed (see description of the list property `species_at_sites`_).

  - For systems that have only species formed by a single chemical symbol, and that have at most one species per chemical symbol, SHOULD use the chemical symbol as species name (e.g., :val:`"Ti"` for titanium, :val:`"O"` for oxygen, etc.)
    However, note that this is OPTIONAL, and client implementations MUST NOT assume that the key corresponds to a chemical symbol, nor assume that if the species name is a valid chemical symbol, that it represents a species with that chemical symbol.
    This means that a species :val:`{"name": "C", "chemical_symbols": ["Ti"], "concentration": [1.0]}` is valid and represents a titanium species (and *not* a carbon species).
  - It is NOT RECOMMENDED that a structure includes species that do not have at least one corresponding site.

- **Examples**:

  - :val:`[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]`: any site with this species is occupied by a Ti atom.
  - :val:`[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]`: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
  - :val:`[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": 88.5} ]`: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability. The mass of this site is (on average) 88.5 a.m.u.
  - :val:`[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": 12.0} ]`: any site with this species is occupied by a carbon isotope with mass 12.
  - :val:`[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": 13.0} ]`: any site with this species is occupied by a carbon isotope with mass 13.""",
    )

    assemblies: Optional[List[Assembly]] = Field(
        None,
        description="""A description of groups of sites that are statistically correlated.
- **Type**: list of dictionary with keys:

  - :property:`sites_in_groups`: list of list of integers (REQUIRED)
  - :property:`group_probabilities`: list of floats (REQUIRED)

- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be :val:`null`.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators.
  - If present, the correct flag MUST be set in the list :property:`structure_features` (see property `structure_features`_).
  - Client implementations MUST check its presence (as its presence changes the interpretation of the structure).
  - If present, it MUST be a list of dictionaries, each of which represents an assembly and MUST have the following two keys:

    - **sites_in_groups**: Index of the sites (0-based) that belong to each group for each assembly.

      Example: :val:`[[1], [2]]`: two groups, one with the second site, one with the third.

      Example: :val:`[[1,2], [3]]`: one group with the second and third site, one with the fourth.

   - **group_probabilities**: Statistical probability of each group. It MUST have the same length as :property:`sites_in_groups`.
     It SHOULD sum to one.
     See below for examples of how to specify the probability of the occurrence of a vacancy.
     The possible reasons for the values not to sum to one are the same as already specified above for the :property:`concentration` of each :property:`species`, see property `species`_.

  - If a site is not present in any group, it means that it is present with 100 % probability (as if no assembly was specified).
  - A site MUST NOT appear in more than one group.

- **Examples** (for each entry of the assemblies list):

  - :val:`{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the first site and the second site never occur at the same time in the unit cell.
    Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.
  - :val:`{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the second and third site are either present together or not present; they form the first group of atoms for this assembly.
    The second group is formed by the fourth site.
    Sites of the first group (the second and the third) are never present at the same time as the fourth site.
    30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

- **Notes**:

  - Assemblies are essential to represent, for instance, the situation where an atom can statistically occupy two different positions (sites).
  - By defining groups, it is possible to represent, e.g., the case where a functional molecule (and not just one atom) is either present or absent (or the case where it it is present in two conformations)
  - Considerations on virtual alloys and on vacancies: In the special case of a virtual alloy, these specifications allow two different, equivalent ways of specifying them.
    For instance, for a site at the origin with 30 % probability of being occupied by Si, 50 % probability of being occupied by Ge, and 20 % of being a vacancy, the following two representations are possible:

    - Using a single species:

      .. code:: jsonc

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


    - Using multiple species and the assemblies:

      .. code:: jsonc

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

  - It is up to the database provider to decide which representation to use, typically depending on the internal format in which the structure is stored.
    However, given a structure identified by a unique ID, the API implementation MUST always provide the same representation for it.
  - The probabilities of occurrence of different assemblies are uncorrelated.
    So, for instance in the following case with two assemblies:

    .. code:: jsonc

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

    Site 0 is present with a probability of 20 % and site 1 with a probability of 80 %. These two sites are correlated (either site 0 or 1 is present). Similarly, site 2 is present with a probability of 30 % and site 3 with a probability of 70 %.
    These two sites are correlated (either site 2 or 3 is present).
    However, the presence or absence of sites 0 and 1 is not correlated with the presence or absence of sites 2 and 3 (in the specific example, the pair of sites (0, 2) can occur with 0.2*0.3 = 6 % probability; the pair (0, 3) with 0.2*0.7 = 14 % probability; the pair (1, 2) with 0.8*0.3 = 24 % probability; and the pair (1, 3) with 0.8*0.7 = 56 % probability).""",
    )

    structure_features: List[str] = Field(
        ...,
        description="""A list of strings that flag which special features are used by the structure.
- **Type**: list of strings
- **Requirements/Conventions**:

  - **Support**: REQUIRED, MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property. Filters on the list MUST support all mandatory HAS-type queries. Filter operators for comparisons on the string components MUST support equality, support for other comparison operators are OPTIONAL.
  - MUST be an empty list if no special features are used.
  - MUST be sorted alphabetically.
  - If a special feature listed below is used, the list MUST contain the corresponding string.
  - If a special feature listed below is not used, the list MUST NOT contain the corresponding string.
  - **List of strings used to indicate special structure features**:

    - :val:`disorder`: This flag MUST be present if any one entry in the :property:`species` list has a :property:`chemical_symbols` list that is longer than 1 element.
    - :val:`unknown_positions`: This flag MUST be present if at least one component of the :property:`cartesian_site_positions` list of lists has value :val:`null`.
    - :val:`assemblies`: This flag MUST be present if the property `assemblies`_ is present.

-  **Examples**: A structure having unknown positions and using assemblies: :val:`["assemblies", "unknown_positions"]`""",
    )

    @validator("elements", each_item=True)
    def element_must_be_chemical_symbol(cls, v):
        if v not in CHEMICAL_SYMBOLS:
            raise ValueError(f"Only chemical symbols are allowed, you passed: {v}")
        return v

    @validator("elements")
    def elements_must_be_alphabetical(cls, v):
        if sorted(v) != v:
            raise ValueError(f"elements must be sorted alphabetically, but is: {v}")
        return v

    @validator("elements_ratios")
    def ratios_must_sum_to_one(cls, v):
        if abs(sum(v) - 1) > EPS:
            raise ValueError(
                f"elements_ratios MUST sum to 1 within floating point accuracy. It sums to: {sum(v)}"
            )
        return v

    @validator("chemical_formula_reduced", "chemical_formula_hill")
    def no_spaces_in_reduced(cls, v):
        if v and " " in v:
            raise ValueError(f"Spaces are not allowed, you passed: {v}")
        return v

    @validator("lattice_vectors", always=True)
    def required_if_dimension_types_has_one(cls, v, values):
        if 1 in values.get("dimension_types", []) and v is None:
            raise ValueError(
                f"lattice_vectors is REQUIRED, since dimension_types is not [0, 0, 0] but is {values.get('dimension_types', 'Not specified')}"
            )

        for dim_type, vector in zip(values.get("dimension_types", []), v):
            if None in vector and dim_type == 1:
                raise ValueError(
                    "Null entries in lattice vectors are only permitted when the corresponding dimension type is 0. "
                    f"Here: dimension_types = {values.get('dimension_types', 'Not specified')}, lattice_vectors = {v}"
                )

        return v

    @validator("nsites")
    def validate_nsites(cls, v, values):
        if v != len(values.get("cartesian_site_positions", [])):
            raise ValueError(
                f"nsites (value: {v}) MUST equal length of cartesian_site_positions (value: {len(values.get('cartesian_site_positions', []))})"
            )
        return v

    @validator("species_at_sites")
    def validate_species_at_sites(cls, v, values):
        if "nsites" not in values:
            raise ValueError(
                "Attribute nsites missing so unable to verify species_at_sites."
            )
        if len(v) != values.get("nsites", 0):
            raise ValueError(
                f"Number of species_at_sites (value: {len(v)}) MUST equal number of sites (value: {values.get('nsites', 'Not specified')})"
            )
        return v

    @validator("species", each_item=True)
    def validate_species(cls, v, values):
        if v.name not in values.get("species_at_sites", []):
            raise ValueError(
                f"{v.name} not found in species_at_sites: {values.get('species_at_sites', 'Not specified')}"
            )
        return v

    @validator("structure_features", always=True)
    def validate_structure_features(cls, v, values):
        if sorted(v) != v:
            raise ValueError(
                f"structure_features MUST be sorted alphabetically, given value: {v}"
            )
        # disorder
        for species in values.get("species", []):
            if len(species.chemical_symbols) > 1:
                if "disorder" not in v:
                    raise ValueError(
                        "disorder MUST be present when any one entry in species has a chemical_symbols list greater than one element"
                    )
                break
        else:
            if "disorder" in v:
                raise ValueError(
                    "disorder MUST NOT be present, since all species' chemical_symbols lists are equal to or less than one element"
                )
        # unknown_positions
        for site in values.get("cartesian_site_positions", []):
            if None in site or float("nan") in site:
                if "unknown_positions" not in v:
                    raise ValueError(
                        "unknown_positions MUST be present when a single component of cartesian_site_positions has value null"
                    )
                break
        else:
            if "unknown_positions" in v:
                raise ValueError(
                    "unknown_positions MUST NOT be present, since there are no null values in cartesian_site_positions"
                )
        # assemblies
        if values.get("assemblies", None) is not None:
            if "assemblies" not in v:
                raise ValueError(
                    "assemblies MUST be present, since the property of the same name is present"
                )
        else:
            if "assemblies" in v:
                raise ValueError(
                    "assemblies MUST NOT be present, since the property of the same name is not present"
                )
        return v


class StructureResource(EntryResource):
    """Representing a structure."""

    type: str = Field(
        "structures",
        const=True,
        description="""The name of the type of an entry. Any entry MUST be able to be fetched using the `base URL <Base URL_>`_ type and ID at the url :endpoint:`<base URL>/<type>/<id>`.
- **Type**: string.
- **Requirements/Conventions**:

  - **Support**: REQUIRED, MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.
  - **Response**: REQUIRED in the response.
  - MUST be an existing entry type.
  - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for :endpoint:`/<type>/<id>` under the versioned base URL.

- **Example**: :val:`"structures"`""",
    )

    attributes: StructureResourceAttributes
