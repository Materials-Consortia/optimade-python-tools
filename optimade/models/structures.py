import re
import warnings
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Annotated, Literal, Optional

from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator

from optimade.models.entries import EntryResource, EntryResourceAttributes
from optimade.models.types import ChemicalSymbol, SymmetryOperation
from optimade.models.utils import (
    ANONYMOUS_ELEMENTS,
    CHEMICAL_FORMULA_REGEXP,
    CHEMICAL_SYMBOLS,
    HM_SYMBOL_REGEXP,
    OptimadeField,
    StrictField,
    SupportLevel,
    reduce_formula,
)
from optimade.warnings import MissingExpectedField

if TYPE_CHECKING:  # pragma: no cover
    from pydantic import ValidationInfo

__all__ = (
    "Vector3D",
    "Periodicity",
    "StructureFeatures",
    "Species",
    "Assembly",
    "StructureResourceAttributes",
    "StructureResource",
)


# Use machine epsilon for single point floating precision
EPS = 2**-23


Vector3D = Annotated[
    list[Annotated[float, BeforeValidator(float)]], Field(min_length=3, max_length=3)
]
Vector3D_unknown = Annotated[
    list[Optional[Annotated[float, BeforeValidator(float)]]],
    Field(min_length=3, max_length=3),
]


class Periodicity(IntEnum):
    """Integer enumeration of dimension_types values"""

    APERIODIC = 0
    PERIODIC = 1


class StructureFeatures(Enum):
    """Enumeration of structure_features values"""

    DISORDER = "disorder"
    IMPLICIT_ATOMS = "implicit_atoms"
    SITE_ATTACHMENTS = "site_attachments"
    ASSEMBLIES = "assemblies"


class Species(BaseModel):
    """A list describing the species of the sites of this structure.

    Species can represent pure chemical elements, virtual-crystal atoms representing a
    statistical occupation of a given site by multiple chemical elements, and/or a
    location to which there are attached atoms, i.e., atoms whose precise location are
    unknown beyond that they are attached to that position (frequently used to indicate
    hydrogen atoms attached to another element, e.g., a carbon with three attached
    hydrogens might represent a methyl group, -CH3).

    - **Examples**:
        - `[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]`: any site with this species is occupied by a Ti atom.
        - `[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]`: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
        - `[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": [0.0, 137.327, 40.078]} ]`: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability. The mass of this site is (on average) 88.5 a.m.u.
        - `[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [12.0]} ]`: any site with this species is occupied by a carbon isotope with mass 12.
        - `[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [13.0]} ]`: any site with this species is occupied by a carbon isotope with mass 13.
        - `[ {"name": "CH3", "chemical_symbols": ["C"], "concentration": [1.0], "attached": ["H"], "nattached": [3]} ]`: any site with this species is occupied by a methyl group, -CH3, which is represented without specifying precise positions of the hydrogen atoms.

    """

    name: Annotated[
        str,
        OptimadeField(
            description="""Gives the name of the species; the **name** value MUST be unique in the `species` list.""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
        ),
    ]

    chemical_symbols: Annotated[
        list[ChemicalSymbol],
        OptimadeField(
            description="""MUST be a list of strings of all chemical elements composing this species. Each item of the list MUST be one of the following:

- a valid chemical-element symbol, or
- the special value `"X"` to represent a non-chemical element, or
- the special value `"vacancy"` to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the `concentration` list, see below).

If any one entry in the `species` list has a `chemical_symbols` list that is longer than 1 element, the correct flag MUST be set in the list `structure_features`.""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
        ),
    ]

    concentration: Annotated[
        list[float],
        OptimadeField(
            description="""MUST be a list of floats, with same length as `chemical_symbols`. The numbers represent the relative concentration of the corresponding chemical symbol in this species. The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

- Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations `1/3` and `2/3`, the concentration might look something like `[0.33333333333, 0.66666666666]`. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
- Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

Note that concentrations are uncorrelated between different site (even of the same species).""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
        ),
    ]

    mass: Annotated[
        list[float] | None,
        OptimadeField(
            description="""If present MUST be a list of floats expressed in a.m.u.
Elements denoting vacancies MUST have masses equal to 0.""",
            unit="a.m.u.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    original_name: Annotated[
        str | None,
        OptimadeField(
            description="""Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    attached: Annotated[
        list[str] | None,
        OptimadeField(
            description="""If provided MUST be a list of length 1 or more of strings of chemical symbols for the elements attached to this site, or "X" for a non-chemical element.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    nattached: Annotated[
        list[int] | None,
        OptimadeField(
            description="""If provided MUST be a list of length 1 or more of integers indicating the number of attached atoms of the kind specified in the value of the :field:`attached` key.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    @field_validator("concentration", "mass", mode="after")
    def validate_concentration_and_mass(
        cls, value: list[float] | None, info: "ValidationInfo"
    ) -> list[float] | None:
        if not value:
            return value

        if info.data.get("chemical_symbols"):
            if len(value) != len(info.data["chemical_symbols"]):
                raise ValueError(
                    f"Length of concentration ({len(value)}) MUST equal length of "
                    f"chemical_symbols ({len(info.data['chemical_symbols'])})"
                )
            return value

        raise ValueError(
            f"Could not validate {info.field_name!r} as 'chemical_symbols' is missing/invalid."
        )

    @field_validator("attached", "nattached", mode="after")
    @classmethod
    def validate_minimum_list_length(
        cls, value: list[str] | list[int] | None
    ) -> list[str] | list[int] | None:
        if value is not None and len(value) < 1:
            raise ValueError(
                "The list's length MUST be 1 or more, instead it was found to be "
                f"{len(value)}"
            )
        return value

    @model_validator(mode="after")
    def attached_nattached_mutually_exclusive(self) -> "Species":
        if (self.attached is None and self.nattached is not None) or (
            self.attached is not None and self.nattached is None
        ):
            raise ValueError(
                f"Either both or none of attached ({self.attached}) and nattached "
                f"({self.nattached}) MUST be set."
            )

        if (
            self.attached is not None
            and self.nattached is not None
            and len(self.attached) != len(self.nattached)
        ):
            raise ValueError(
                f"attached ({self.attached}) and nattached ({self.nattached}) MUST be "
                "lists of equal length."
            )

        return self


class Assembly(BaseModel):
    """A description of groups of sites that are statistically correlated.

    - **Examples** (for each entry of the assemblies list):
        - `{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the first site and the second site never occur at the same time in the unit cell.
          Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.
        - `{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the second and third site are either present together or not present; they form the first group of atoms for this assembly.
          The second group is formed by the fourth site. Sites of the first group (the second and the third) are never present at the same time as the fourth site.
          30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

    """

    sites_in_groups: Annotated[
        list[list[int]],
        OptimadeField(
            description="""Index of the sites (0-based) that belong to each group for each assembly.

- **Examples**:
    - `[[1], [2]]`: two groups, one with the second site, one with the third.
    - `[[1,2], [3]]`: one group with the second and third site, one with the fourth.""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
        ),
    ]

    group_probabilities: Annotated[
        list[float],
        OptimadeField(
            description="""Statistical probability of each group. It MUST have the same length as `sites_in_groups`.
It SHOULD sum to one.
See below for examples of how to specify the probability of the occurrence of a vacancy.
The possible reasons for the values not to sum to one are the same as already specified above for the `concentration` of each `species`.""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
        ),
    ]

    @field_validator("sites_in_groups", mode="after")
    @classmethod
    def validate_sites_in_groups(cls, value: list[list[int]]) -> list[list[int]]:
        sites = []
        for group in value:
            sites.extend(group)
        if len(set(sites)) != len(sites):
            raise ValueError(
                f"A site MUST NOT appear in more than one group. Given value: {value}"
            )
        return value

    @model_validator(mode="after")
    def check_self_consistency(self) -> "Assembly":
        if len(self.group_probabilities) != len(self.sites_in_groups):
            raise ValueError(
                f"sites_in_groups and group_probabilities MUST be of same length, "
                f"but are {len(self.sites_in_groups)} and {len(self.group_probabilities)}, "
                "respectively"
            )
        return self


CORRELATED_STRUCTURE_FIELDS = (
    {"dimension_types", "nperiodic_dimensions"},
    {"cartesian_site_positions", "species_at_sites"},
    {"nsites", "cartesian_site_positions"},
    {"species_at_sites", "species"},
)


class StructureResourceAttributes(EntryResourceAttributes):
    """This class contains the Field for the attributes used to represent a structure, e.g. unit cell, atoms, positions."""

    elements: Annotated[
        list[str] | None,
        OptimadeField(
            description="""The chemical symbols of the different elements present in the structure.

- **Type**: list of strings.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - The strings are the chemical symbols, i.e., either a single uppercase letter or an uppercase letter followed by a number of lowercase letters.
    - The order MUST be alphabetical.
    - MUST refer to the same elements in the same order, and therefore be of the same length, as `elements_ratios`, if the latter is provided.
    - Note: This property SHOULD NOT contain the string "X" to indicate non-chemical elements or "vacancy" to indicate vacancies (in contrast to the field `chemical_symbols` for the `species` property).

- **Examples**:
    - `["Si"]`
    - `["Al","O","Si"]`

- **Query examples**:
    - A filter that matches all records of structures that contain Si, Al **and** O, and possibly other elements: `elements HAS ALL "Si", "Al", "O"`.
    - To match structures with exactly these three elements, use `elements HAS ALL "Si", "Al", "O" AND elements LENGTH 3`.
    - Note: length queries on this property can be equivalently formulated by filtering on the `nelements`_ property directly.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
        ),
    ] = None

    nelements: Annotated[
        int | None,
        OptimadeField(
            description="""Number of different elements in the structure as an integer.

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - MUST be equal to the lengths of the list properties `elements` and `elements_ratios`, if they are provided.

- **Examples**:
    - `3`

- **Querying**:
    - Note: queries on this property can equivalently be formulated using `elements LENGTH`.
    - A filter that matches structures that have exactly 4 elements: `nelements=4`.
    - A filter that matches structures that have between 2 and 7 elements: `nelements>=2 AND nelements<=7`.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
        ),
    ] = None

    elements_ratios: Annotated[
        list[float] | None,
        OptimadeField(
            description="""Relative proportions of different elements in the structure.

- **Type**: list of floats

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - Composed by the proportions of elements in the structure as a list of floating point numbers.
    - The sum of the numbers MUST be 1.0 (within floating point accuracy)
    - MUST refer to the same elements in the same order, and therefore be of the same length, as `elements`, if the latter is provided.

- **Examples**:
    - `[1.0]`
    - `[0.3333333333333333, 0.2222222222222222, 0.4444444444444444]`

- **Query examples**:
    - Note: Useful filters can be formulated using the set operator syntax for correlated values.
      However, since the values are floating point values, the use of equality comparisons is generally inadvisable.
    - OPTIONAL: a filter that matches structures where approximately 1/3 of the atoms in the structure are the element Al is: `elements:elements_ratios HAS ALL "Al":>0.3333, "Al":<0.3334`.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
        ),
    ] = None

    chemical_formula_descriptive: Annotated[
        str | None,
        OptimadeField(
            description="""The chemical formula for a structure as a string in a form chosen by the API implementation.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - The chemical formula is given as a string consisting of properly capitalized element symbols followed by integers or decimal numbers, balanced parentheses, square, and curly brackets `(`,`)`, `[`,`]`, `{`, `}`, commas, the `+`, `-`, `:` and `=` symbols. The parentheses are allowed to be followed by a number. Spaces are allowed anywhere except within chemical symbols. The order of elements and any groupings indicated by parentheses or brackets are chosen freely by the API implementation.
    - The string SHOULD be arithmetically consistent with the element ratios in the `chemical_formula_reduced` property.
    - It is RECOMMENDED, but not mandatory, that symbols, parentheses and brackets, if used, are used with the meanings prescribed by [IUPAC's Nomenclature of Organic Chemistry](https://www.qmul.ac.uk/sbcs/iupac/bibliog/blue.html).

- **Examples**:
    - `"(H2O)2 Na"`
    - `"NaCl"`
    - `"CaCO3"`
    - `"CCaO3"`
    - `"(CH3)3N+ - [CH2]2-OH = Me3N+ - CH2 - CH2OH"`

- **Query examples**:
    - Note: the free-form nature of this property is likely to make queries on it across different databases inconsistent.
    - A filter that matches an exactly given formula: `chemical_formula_descriptive="(H2O)2 Na"`.
    - A filter that does a partial match: `chemical_formula_descriptive CONTAINS "H2O"`.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
        ),
    ] = None

    chemical_formula_reduced: Annotated[
        str | None,
        OptimadeField(
            description="""The reduced chemical formula for a structure as a string with element symbols and integer chemical proportion numbers.
The proportion number MUST be omitted if it is 1.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property.
      However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).
      Intricate queries on formula components are instead suggested to be formulated using set-type filter operators on the multi valued `elements` and `elements_ratios` properties.
    - Element symbols MUST have proper capitalization (e.g., `"Si"`, not `"SI"` for "silicon").
    - Elements MUST be placed in alphabetical order, followed by their integer chemical proportion number.
    - For structures with no partial occupation, the chemical proportion numbers are the smallest integers for which the chemical proportion is exactly correct.
    - For structures with partial occupation, the chemical proportion numbers are integers that within reasonable approximation indicate the correct chemical proportions. The precise details of how to perform the rounding is chosen by the API implementation.
    - No spaces or separators are allowed.

- **Examples**:
    - `"H2NaO"`
    - `"ClNa"`
    - `"CCaO3"`

- **Query examples**:
    - A filter that matches an exactly given formula is `chemical_formula_reduced="H2NaO"`.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            pattern=CHEMICAL_FORMULA_REGEXP,
        ),
    ] = None

    chemical_formula_hill: Annotated[
        str | None,
        OptimadeField(
            description="""The chemical formula for a structure in [Hill form](https://dx.doi.org/10.1021/ja02046a005) with element symbols followed by integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, only a subset of the filter features MAY be supported.
    - The overall scale factor of the chemical proportions is chosen such that the resulting values are integers that indicate the most chemically relevant unit of which the system is composed.
      For example, if the structure is a repeating unit cell with four hydrogens and four oxygens that represents two hydroperoxide molecules, `chemical_formula_hill` is `"H2O2"` (i.e., not `"HO"`, nor `"H4O4"`).
    - If the chemical insight needed to ascribe a Hill formula to the system is not present, the property MUST be handled as unset.
    - Element symbols MUST have proper capitalization (e.g., `"Si"`, not `"SI"` for "silicon").
    - Elements MUST be placed in [Hill order](https://dx.doi.org/10.1021/ja02046a005), followed by their integer chemical proportion number.
      Hill order means: if carbon is present, it is placed first, and if also present, hydrogen is placed second.
      After that, all other elements are ordered alphabetically.
      If carbon is not present, all elements are ordered alphabetically.
    - If the system has sites with partial occupation and the total occupations of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.
    - No spaces or separators are allowed.

- **Examples**:
    - `"H2O2"`

- **Query examples**:
    - A filter that matches an exactly given formula is `chemical_formula_hill="H2O2"`.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            pattern=CHEMICAL_FORMULA_REGEXP,
        ),
    ] = None

    chemical_formula_anonymous: Annotated[
        str | None,
        OptimadeField(
            description="""The anonymous formula is the `chemical_formula_reduced`, but where the elements are instead first ordered by their chemical proportion number, and then, in order left to right, replaced by anonymous symbols A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property.
      However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).

- **Examples**:
    - `"A2B"`
    - `"A42B42C16D12E10F9G5"`

- **Querying**:
    - A filter that matches an exactly given formula is `chemical_formula_anonymous="A2B"`.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            pattern=CHEMICAL_FORMULA_REGEXP,
        ),
    ] = None

    dimension_types: Annotated[
        list[Periodicity] | None,
        OptimadeField(
            min_length=3,
            max_length=3,
            title="Dimension Types",
            description="""List of three integers.
For each of the three directions indicated by the three lattice vectors (see property `lattice_vectors`), this list indicates if the direction is periodic (value `1`) or non-periodic (value `0`).
Note: the elements in this list each refer to the direction of the corresponding entry in `lattice_vectors` and *not* the Cartesian x, y, z directions.

- **Type**: list of integers.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - MUST be a list of length 3.
    - Each integer element MUST assume only the value 0 or 1.

- **Examples**:
    - For a molecule: `[0, 0, 0]`
    - For a wire along the direction specified by the third lattice vector: `[0, 0, 1]`
    - For a 2D surface/slab, periodic on the plane defined by the first and third lattice vectors: `[1, 0, 1]`
    - For a bulk 3D system: `[1, 1, 1]`""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    nperiodic_dimensions: Annotated[
        int | None,
        OptimadeField(
            description="""An integer specifying the number of periodic dimensions in the structure, equivalent to the number of non-zero entries in `dimension_types`.

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - The integer value MUST be between 0 and 3 inclusive and MUST be equal to the sum of the items in the `dimension_types` property.
    - This property only reflects the treatment of the lattice vectors provided for the structure, and not any physical interpretation of the dimensionality of its contents.

- **Examples**:
    - `2` should be indicated in cases where `dimension_types` is any of `[1, 1, 0]`, `[1, 0, 1]`, `[0, 1, 1]`.

- **Query examples**:
    - Match only structures with exactly 3 periodic dimensions: `nperiodic_dimensions=3`
    - Match all structures with 2 or fewer periodic dimensions: `nperiodic_dimensions<=2`""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
        ),
    ] = None

    lattice_vectors: Annotated[
        list[Vector3D_unknown] | None,
        OptimadeField(
            min_length=3,
            max_length=3,
            description="""The three lattice vectors in Cartesian coordinates, in ångström (Å).

- **Type**: list of list of floats or unknown values.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, filters MAY support only a subset of comparison operators.
    - MUST be a list of three vectors *a*, *b*, and *c*, where each of the vectors MUST BE a list of the vector's coordinates along the x, y, and z Cartesian coordinates.
      (Therefore, the first index runs over the three lattice vectors and the second index runs over the x, y, z Cartesian coordinates).
    - For databases that do not define an absolute Cartesian system (e.g., only defining the length and angles between vectors), the first lattice vector SHOULD be set along *x* and the second on the *xy*-plane.
    - MUST always contain three vectors of three coordinates each, independently of the elements of property `dimension_types`.
      The vectors SHOULD by convention be chosen so the determinant of the `lattice_vectors` matrix is different from zero.
      The vectors in the non-periodic directions have no significance beyond fulfilling these requirements.
    - The coordinates of the lattice vectors of non-periodic dimensions (i.e., those dimensions for which `dimension_types` is `0`) MAY be given as a list of all `null` values.
        If a lattice vector contains the value `null`, all coordinates of that lattice vector MUST be `null`.

- **Examples**:
    - `[[4.0,0.0,0.0],[0.0,4.0,0.0],[0.0,1.0,4.0]]` represents a cell, where the first vector is `(4, 0, 0)`, i.e., a vector aligned along the `x` axis of length 4 Å; the second vector is `(0, 4, 0)`; and the third vector is `(0, 1, 4)`.""",
            unit="Å",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    space_group_symmetry_operations_xyz: Annotated[
        list[SymmetryOperation] | None,
        OptimadeField(
            description="""A list of symmetry operations given as general position x, y and z coordinates in algebraic form.

- **Type**: list of strings

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
      - The property is RECOMMENDED if coordinates are returned in a form to which these operations can or must be applied (e.g. fractional atom coordinates of an asymmetric unit).
      - The property is REQUIRED if symmetry operations are necessary to reconstruct the full model of the material and no other symmetry information (e.g., the Hall symbol) is provided that would allow the user to derive symmetry operations unambiguously.
    - **Query***: Support for queries on this property is not required and in fact is NOT RECOMMENDED.
    - MUST be `null` if `nperiodic_dimensions` is equal to 0.
    - Each symmetry operation is described by a string that gives that symmetry operation in Jones' faithful representation (Bradley & Cracknell, 1972: pp. 35-37), adapted for computer string notation.
    - The letters `x`, `y` and `z` that are typesetted with overbars in printed text represent coordinate values multiplied by -1 and are encoded as `-x`, `-y` and `-z`, respectively.
    - The syntax of the strings representing symmetry operations MUST conform to regular expressions given in appendix The Symmetry Operation String Regular Expressions.
    - The interpretation of the strings MUST follow the conventions of the IUCr CIF core dictionary (IUCr, 2023). In particular, this property MUST explicitly provide all symmetry operations needed to generate all the atoms in the unit cell from the atoms in the asymmetric unit, for the setting used.
    - This symmetry operation set MUST always include the `x,y,z` identity operation.
    - The symmetry operations are to be applied to fractional atom coordinates. In case only Cartesian coordinates are available, these Cartesian coordinates must be converted to fractional coordinates before the application of the provided symmetry operations.
    - If the symmetry operation list is present, it MUST be compatible with other space group specifications (e.g. the ITC space group number, the Hall symbol, the Hermann-Mauguin symbol) if these are present.

- **Examples**:
    - Space group operations for the space group with ITC number 3 (H-M symbol `P 2`, extended H-M symbol `P 1 2 1`, Hall symbol `P 2y`): `["x,y,z", "-x,y,-z"]`
    - Space group operations for the space group with ITC number 5 (H-M symbol `C 2`, extended H-M symbol `C 1 2 1`, Hall symbol `C 2y`): `["x,y,z", "-x,y,-z", "x+1/2,y+1/2,z", "-x+1/2,y+1/2,-z"]`

- **Notes**: The list of space group symmetry operations applies to the whole periodic array of atoms and together with the lattice translations given in the `lattice_vectors` property provides the necessary information to reconstruct all atom site positions of the periodic material.
  Thus, the symmetry operations described in this property are only applicable to material models with at least one periodic dimension.
  This property is not meant to represent arbitrary symmetries of molecules, non-periodic (finite) collections of atoms or non-crystallographic symmetry.

- **Bibliographic References**:
  - Bradley, C. J. and Cracknell, A. P. (1972) The Mathematical Theory of Symmetry in Solids. Oxford, Clarendon Press (paperback edition 2010) 745 p. ISBN 978-0-19-958258-7.
  - IUCr (2023) Core dictionary (coreCIF) version 2.4.5; data name `_space_group_symop_operation_xyz`. Available from: https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_symop_operation_xyz.html [Accessed 2023-06-18T16:46+03:00].""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    space_group_symbol_hall: Annotated[
        str | None,
        OptimadeField(
            description="""A Hall space group symbol representing the symmetry of the structure as defined in (Hall, 1981, 1981a).

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - The change-of-basis operations are used as defined in the International Tables of Crystallography (ITC) Vol. B, Sect. 1.4, Appendix A1.4.2 (IUCr, 2001).
    - Each component of the Hall symbol MUST be separated by a single space symbol.
    - If there exists a standard Hall symbol which represents the symmetry it SHOULD be used.
    - MUST be `null` if `nperiodic_dimensions` is not equal to 3.

- **Examples**:
    - Space group symbols with explicit origin (the Hall symbols):
        - `P 2c -2ac`
        - `I 4bd 2ab 3`
    - Space group symbols with change-of-basis operations:
        - `P 2yb (-1/2*x+z,1/2*x,y)`
        - `-I 4 2 (1/2*x+1/2*y,-1/2*x+1/2*y,z)`

- **Bibliographic References**:
    - Hall, S. R. (1981) Space-group notation with an explicit origin. Acta Crystallographica Section A, 37, 517-525, International Union of Crystallography (IUCr), DOI: https://doi.org/10.1107/s0567739481001228
    - Hall, S. R. (1981a) Space-group notation with an explicit origin; erratum. Acta Crystallographica Section A, 37, 921-921, International Union of Crystallography (IUCr), DOI: https://doi.org/10.1107/s0567739481001976
    - IUCr (2001). International Tables for Crystallography vol. B. Reciprocal Space. Ed. U. Shmueli. 2-nd edition. Dordrecht/Boston/London, Kluwer Academic Publishers.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    space_group_symbol_hermann_mauguin: Annotated[
        str | None,
        OptimadeField(
            description="""A human- and machine-readable string containing the short Hermann-Mauguin (H-M) symbol which specifies the space group of the structure in the response.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - The H-M symbol SHOULD aim to convey the closest representation of the symmetry information that can be specified using the short format used in the International Tables for Crystallography vol. A (IUCr, 2005), Table 4.3.2.1 as described in the accompanying text.
    - The symbol MAY be a non-standard short H-M symbol.
    - The H-M symbol does not unambiguously communicate the axis, cell, and origin choice, and the given symbol SHOULD NOT be amended to convey this information.
    - To encode as character strings, the following adaptations MUST be made when representing H-M symbols given in their typesetted form:
        - the overbar above the numbers MUST be changed to the minus sign in front of the digit (e.g. '-2');
        - subscripts that denote screw axes are written as digits immediately after the axis designator without a space (e.g. 'P 32')
        - the space group generators MUST be separated by a single space (e.g. 'P 21 21 2');
        - there MUST be no spaces in the space group generator designation (i.e. use 'P 21/m', not the 'P 21 / m');

- **Examples**:
    - `C 2`
    - `P 21 21 21`

- **Bibliographic References**:
    - IUCr (2005). International Tables for Crystallography vol. A. Space-Group Symmetry. Ed. Theo Hahn. 5-th edition. Dordrecht, Springer.
""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            pattern=HM_SYMBOL_REGEXP,
        ),
    ] = None

    space_group_symbol_hermann_mauguin_extended: Annotated[
        str | None,
        OptimadeField(
            description="""A human- and machine-readable string containing the extended Hermann-Mauguin (H-M) symbol which specifies the space group of the structure in the response.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - The H-M symbols SHOULD be given as specified in the International Tables for Crystallography vol. A (IUCr, 2005), Table 4.3.2.1.
    - The change-of-basis operation SHOULD be provided for the non-standard axis and cell choices.
    - The extended H-M symbol does not unambiguously communicate the origin choice, and the given symbol SHOULD NOT be amended to convey this information.
    - The description of the change-of-basis SHOULD follow conventions of the ITC Vol. B, Sect. 1.4, Appendix A1.4.2 (IUCr, 2001).
    - The same character string encoding conventions MUST be used as for the specification of the `space_group_symbol_hermann_mauguin` property.

- **Examples**:
    - `C 1 2 1`

- **Bibliographic References**:
    - IUCr (2001). International Tables for Crystallography vol. B. Reciprocal Space. Ed. U. Shmueli. 2-nd edition. Dordrecht/Boston/London, Kluwer Academic Publishers.
    - IUCr (2005). International Tables for Crystallography vol. A. Space-Group Symmetry. Ed. Theo Hahn. 5-th edition. Dordrecht, Springer.

""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            pattern=HM_SYMBOL_REGEXP,
        ),
    ] = None

    space_group_it_number: Annotated[
        int | None,
        OptimadeField(
            description="""Space group number which specifies the space group of the structure as defined in the International Tables for Crystallography Vol. A. (IUCr, 2005).

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - The integer value MUST be between 1 and 230.
    - MUST be null if `nperiodic_dimensions` is not equal to 3.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            ge=1,
            le=230,
        ),
    ] = None

    cartesian_site_positions: Annotated[
        list[Vector3D] | None,
        OptimadeField(
            description="""Cartesian positions of each site in the structure.
A site is usually used to describe positions of atoms; what atoms can be encountered at a given site is conveyed by the `species_at_sites` property, and the species themselves are described in the `species` property.

- **Type**: list of list of floats

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, filters MAY support only a subset of comparison operators.
    - It MUST be a list of length equal to the number of sites in the structure, where every element is a list of the three Cartesian coordinates of a site expressed as float values in the unit angstrom (Å).
    - An entry MAY have multiple sites at the same Cartesian position (for a relevant use of this, see e.g., the property `assemblies`).

- **Examples**:
    - `[[0,0,0],[0,0,2]]` indicates a structure with two sites, one sitting at the origin and one along the (positive) *z*-axis, 2 Å away from the origin.""",
            unit="Å",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    nsites: Annotated[
        int | None,
        OptimadeField(
            description="""An integer specifying the length of the `cartesian_site_positions` property.

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.

- **Examples**:
    - `42`

- **Query examples**:
    - Match only structures with exactly 4 sites: `nsites=4`
    - Match structures that have between 2 and 7 sites: `nsites>=2 AND nsites<=7`""",
            queryable=SupportLevel.MUST,
            support=SupportLevel.SHOULD,
        ),
    ] = None

    species: Annotated[
        list[Species] | None,
        OptimadeField(
            description="""A list describing the species of the sites of this structure.
Species can represent pure chemical elements, virtual-crystal atoms representing a statistical occupation of a given site by multiple chemical elements, and/or a location to which there are attached atoms, i.e., atoms whose precise location are unknown beyond that they are attached to that position (frequently used to indicate hydrogen atoms attached to another element, e.g., a carbon with three attached hydrogens might represent a methyl group, -CH3).

- **Type**: list of dictionary with keys:
    - `name`: string (REQUIRED)
    - `chemical_symbols`: list of strings (REQUIRED)
    - `concentration`: list of float (REQUIRED)
    - `attached`: list of strings (REQUIRED)
    - `nattached`: list of integers (OPTIONAL)
    - `mass`: list of floats (OPTIONAL)
    - `original_name`: string (OPTIONAL).

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
        If supported, filters MAY support only a subset of comparison operators.
    - Each list member MUST be a dictionary with the following keys:
        - **name**: REQUIRED; gives the name of the species; the **name** value MUST be unique in the `species` list;
        - **chemical_symbols**: REQUIRED; MUST be a list of strings of all chemical elements composing this species.
          Each item of the list MUST be one of the following:
            - a valid chemical-element symbol, or
            - the special value `"X"` to represent a non-chemical element, or
            - the special value `"vacancy"` to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the `concentration` list, see below).

          If any one entry in the `species` list has a `chemical_symbols` list that is longer than 1 element, the correct flag MUST be set in the list `structure_features`.

        - **concentration**: REQUIRED; MUST be a list of floats, with same length as `chemical_symbols`.
          The numbers represent the relative concentration of the corresponding chemical symbol in this species.
          The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

            - Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations `1/3` and `2/3`, the concentration might look something like `[0.33333333333, 0.66666666666]`. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
            - Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

            Note that concentrations are uncorrelated between different sites (even of the same species).

        - **attached**: OPTIONAL; if provided MUST be a list of length 1 or more of strings of chemical symbols for the elements attached to this site, or "X" for a non-chemical element.

        - **nattached**: OPTIONAL; if provided MUST be a list of length 1 or more of integers indicating the number of attached atoms of the kind specified in the value of the `attached` key.

          The implementation MUST include either both or none of the `attached` and `nattached` keys, and if they are provided, they MUST be of the same length.
          Furthermore, if they are provided, the `structure_features` property MUST include the string `site_attachments`.

        - **mass**: OPTIONAL. If present MUST be a list of floats, with the same length as `chemical_symbols`, providing element masses expressed in a.m.u.
          Elements denoting vacancies MUST have masses equal to 0.

        - **original_name**: OPTIONAL. Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

          Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation.

          The main use of this field is for source databases that use species names, containing characters that are not allowed (see description of the list property `species_at_sites`).

    - For systems that have only species formed by a single chemical symbol, and that have at most one species per chemical symbol, SHOULD use the chemical symbol as species name (e.g., `"Ti"` for titanium, `"O"` for oxygen, etc.)
      However, note that this is OPTIONAL, and client implementations MUST NOT assume that the key corresponds to a chemical symbol, nor assume that if the species name is a valid chemical symbol, that it represents a species with that chemical symbol.
      This means that a species `{"name": "C", "chemical_symbols": ["Ti"], "concentration": [1.0]}` is valid and represents a titanium species (and *not* a carbon species).
    - It is NOT RECOMMENDED that a structure includes species that do not have at least one corresponding site.

- **Examples**:
    - `[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]`: any site with this species is occupied by a Ti atom.
    - `[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]`: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
    - `[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": [0.0, 137.327, 40.078]} ]`: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability. The mass of this site is (on average) 88.5 a.m.u.
    - `[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [12.0]} ]`: any site with this species is occupied by a carbon isotope with mass 12.
    - `[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [13.0]} ]`: any site with this species is occupied by a carbon isotope with mass 13.
    - `[ {"name": "CH3", "chemical_symbols": ["C"], "concentration": [1.0], "attached": ["H"], "nattached": [3]} ]`: any site with this species is occupied by a methyl group, -CH3, which is represented without specifying precise positions of the hydrogen atoms.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    species_at_sites: Annotated[
        list[str] | None,
        OptimadeField(
            description="""Name of the species at each site (where values for sites are specified with the same order of the property `cartesian_site_positions`).
The properties of the species are found in the property `species`.

- **Type**: list of strings.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, filters MAY support only a subset of comparison operators.
    - MUST have length equal to the number of sites in the structure (first dimension of the list property `cartesian_site_positions`).
    - Each species name mentioned in the `species_at_sites` list MUST be described in the list property `species` (i.e. for each value in the `species_at_sites` list there MUST exist exactly one dictionary in the `species` list with the `name` attribute equal to the corresponding `species_at_sites` value).
    - Each site MUST be associated only to a single species.
      **Note**: However, species can represent mixtures of atoms, and multiple species MAY be defined for the same chemical element.
      This latter case is useful when different atoms of the same type need to be grouped or distinguished, for instance in simulation codes to assign different initial spin states.

- **Examples**:
    - `["Ti","O2"]` indicates that the first site is hosting a species labeled `"Ti"` and the second a species labeled `"O2"`.
    - `["Ac", "Ac", "Ag", "Ir"]` indicating the first two sites contains the `"Ac"` species, while the third and fourth sites contain the `"Ag"` and `"Ir"` species, respectively.""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    assemblies: Annotated[
        list[Assembly] | None,
        OptimadeField(
            description="""A description of groups of sites that are statistically correlated.

- **Type**: list of dictionary with keys:
    - `sites_in_groups`: list of list of integers (REQUIRED)
    - `group_probabilities`: list of floats (REQUIRED)

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
        If supported, filters MAY support only a subset of comparison operators.
    - The property SHOULD be `null` for entries that have no partial occupancies.
    - If present, the correct flag MUST be set in the list `structure_features`.
    - Client implementations MUST check its presence (as its presence changes the interpretation of the structure).
    - If present, it MUST be a list of dictionaries, each of which represents an assembly and MUST have the following two keys:
        - **sites_in_groups**: Index of the sites (0-based) that belong to each group for each assembly.

            Example: `[[1], [2]]`: two groups, one with the second site, one with the third.
            Example: `[[1,2], [3]]`: one group with the second and third site, one with the fourth.

        - **group_probabilities**: Statistical probability of each group. It MUST have the same length as `sites_in_groups`.
            It SHOULD sum to one.
            See below for examples of how to specify the probability of the occurrence of a vacancy.
            The possible reasons for the values not to sum to one are the same as already specified above for the `concentration` of each `species`.

    - If a site is not present in any group, it means that it is present with 100 % probability (as if no assembly was specified).
    - A site MUST NOT appear in more than one group.

- **Examples** (for each entry of the assemblies list):
    - `{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the first site and the second site never occur at the same time in the unit cell.
        Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.
    - `{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the second and third site are either present together or not present; they form the first group of atoms for this assembly.
        The second group is formed by the fourth site.
        Sites of the first group (the second and the third) are never present at the same time as the fourth site.
        30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

- **Notes**:
    - Assemblies are essential to represent, for instance, the situation where an atom can statistically occupy two different positions (sites).

    - By defining groups, it is possible to represent, e.g., the case where a functional molecule (and not just one atom) is either present or absent (or the case where it it is present in two conformations)

    - Considerations on virtual alloys and on vacancies: In the special case of a virtual alloy, these specifications allow two different, equivalent ways of specifying them.
        For instance, for a site at the origin with 30 % probability of being occupied by Si, 50 % probability of being occupied by Ge, and 20 % of being a vacancy, the following two representations are possible:

        - Using a single species:
            ```json
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

        - Using multiple species and the assemblies:
            ```json
            {
              "cartesian_site_positions": [ [0,0,0], [0,0,0], [0,0,0] ],
              "species_at_sites": ["Si", "Ge", "vac"],
              "species": [
                { "name": "Si", "chemical_symbols": ["Si"], "concentration": [1.0] },
                { "name": "Ge", "chemical_symbols": ["Ge"], "concentration": [1.0] },
                { "name": "vac", "chemical_symbols": ["vacancy"], "concentration": [1.0] }
              ],
              "assemblies": [
                {
              "sites_in_groups": [ [0], [1], [2] ],
              "group_probabilities": [0.3, 0.5, 0.2]
                }
              ]
              // ...
            }
            ```

    - It is up to the database provider to decide which representation to use, typically depending on the internal format in which the structure is stored.
        However, given a structure identified by a unique ID, the API implementation MUST always provide the same representation for it.

    - The probabilities of occurrence of different assemblies are uncorrelated.
        So, for instance in the following case with two assemblies:
        ```json
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

        Site 0 is present with a probability of 20 % and site 1 with a probability of 80 %. These two sites are correlated (either site 0 or 1 is present). Similarly, site 2 is present with a probability of 30 % and site 3 with a probability of 70 %.
        These two sites are correlated (either site 2 or 3 is present).
        However, the presence or absence of sites 0 and 1 is not correlated with the presence or absence of sites 2 and 3 (in the specific example, the pair of sites (0, 2) can occur with 0.2*0.3 = 6 % probability; the pair (0, 3) with 0.2*0.7 = 14 % probability; the pair (1, 2) with 0.8*0.3 = 24 % probability; and the pair (1, 3) with 0.8*0.7 = 56 % probability).""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    structure_features: Annotated[
        list[StructureFeatures],
        OptimadeField(
            title="Structure Features",
            description="""A list of strings that flag which special features are used by the structure.

- **Type**: list of strings

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property.
    Filters on the list MUST support all mandatory HAS-type queries.
    Filter operators for comparisons on the string components MUST support equality, support for other comparison operators are OPTIONAL.
    - MUST be an empty list if no special features are used.
    - MUST be sorted alphabetically.
    - If a special feature listed below is used, the list MUST contain the corresponding string.
    - If a special feature listed below is not used, the list MUST NOT contain the corresponding string.
    - **List of strings used to indicate special structure features**:
        - `disorder`: this flag MUST be present if any one entry in the `species` list has a `chemical_symbols` list that is longer than 1 element.
        - `implicit_atoms`: this flag MUST be present if the structure contains atoms that are not assigned to sites via the property `species_at_sites` (e.g., because their positions are unknown).
           When this flag is present, the properties related to the chemical formula will likely not match the type and count of atoms represented by the `species_at_sites`, `species` and `assemblies` properties.
        - `site_attachments`: this flag MUST be present if any one entry in the `species` list includes `attached` and `nattached`.
        - `assemblies`: this flag MUST be present if the property `assemblies` is present.

- **Examples**: A structure having implicit atoms and using assemblies: `["assemblies", "implicit_atoms"]`""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.MUST,
        ),
    ]

    @model_validator(mode="after")
    def warn_on_missing_correlated_fields(self) -> "StructureResourceAttributes":
        """Emit warnings if a field takes a null value when a value
        was expected based on the value/nullity of another field.
        """
        accumulated_warnings = []
        for field_set in CORRELATED_STRUCTURE_FIELDS:
            missing_fields = {
                field for field in field_set if getattr(self, field, None) is None
            }
            if missing_fields and len(missing_fields) != len(field_set):
                accumulated_warnings += [
                    f"Structure with attributes {self} is missing fields "
                    f"{missing_fields} which are required if "
                    f"{field_set - missing_fields} are present."
                ]

        for warn in accumulated_warnings:
            warnings.warn(warn, MissingExpectedField)

        return self

    @field_validator("chemical_formula_reduced", "chemical_formula_hill", mode="after")
    @classmethod
    def check_ordered_formula(
        cls, value: str | None, info: "ValidationInfo"
    ) -> str | None:
        if value is None:
            return value

        elements = re.findall(r"[A-Z][a-z]?", value)
        expected_elements = sorted(elements)

        if info.field_name == "chemical_formula_hill":
            # Make sure C is first (and H is second, if present along with C).
            if "C" in expected_elements:
                expected_elements = sorted(
                    expected_elements,
                    key=lambda elem: {"C": "0", "H": "1"}.get(elem, elem),
                )

        if any(elem not in CHEMICAL_SYMBOLS for elem in elements):
            raise ValueError(
                f"Cannot use unknown chemical symbols {[elem for elem in elements if elem not in CHEMICAL_SYMBOLS]} in {info.field_name!r}"
            )

        if expected_elements != elements:
            order = (
                "Hill" if info.field_name == "chemical_formula_hill" else "alphabetical"
            )
            raise ValueError(
                f"Elements in {info.field_name!r} must appear in {order} order: {expected_elements} not {elements}."
            )

        return value

    @field_validator("chemical_formula_anonymous", mode="after")
    @classmethod
    def check_anonymous_formula(cls, value: str | None) -> str | None:
        if value is None:
            return value

        elements = tuple(re.findall(r"[A-Z][a-z]*", value))
        numbers = re.split(r"[A-Z][a-z]*", value)[1:]
        numbers = [int(i) if i else 1 for i in numbers]

        expected_labels = ANONYMOUS_ELEMENTS[: len(elements)]
        expected_numbers = sorted(numbers, reverse=True)

        if expected_numbers != numbers:
            raise ValueError(
                f"'chemical_formula_anonymous' {value} has wrong order: elements with "
                f"highest proportion should appear first: {numbers} vs expected "
                f"{expected_numbers}"
            )
        if elements != expected_labels:
            raise ValueError(
                f"'chemical_formula_anonymous' {value} has wrong labels: {elements} vs"
                f" expected {expected_labels}."
            )

        return value

    @field_validator(
        "chemical_formula_anonymous", "chemical_formula_reduced", mode="after"
    )
    @classmethod
    def check_reduced_formulae(
        cls, value: str | None, info: "ValidationInfo"
    ) -> str | None:
        if value is None:
            return value

        reduced_formula = reduce_formula(value)
        if reduced_formula != value:
            raise ValueError(
                f"{info.field_name} {value!r} is not properly reduced: expected "
                f"{reduced_formula!r}."
            )

        return value

    @field_validator("elements", mode="after")
    @classmethod
    def elements_must_be_alphabetical(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value

        if sorted(value) != value:
            raise ValueError(f"elements must be sorted alphabetically, but is: {value}")
        return value

    @field_validator("elements_ratios", mode="after")
    @classmethod
    def ratios_must_sum_to_one(cls, value: list[float] | None) -> list[float] | None:
        if value is None:
            return value

        if abs(sum(value) - 1) > EPS:
            raise ValueError(
                "elements_ratios MUST sum to 1 within (at least single precision) "
                f"floating point accuracy. It sums to: {sum(value)}"
            )
        return value

    @model_validator(mode="after")
    def check_dimensions_types_dependencies(self) -> "StructureResourceAttributes":
        if self.nperiodic_dimensions is not None:
            if self.dimension_types and self.nperiodic_dimensions != sum(
                self.dimension_types
            ):
                raise ValueError(
                    f"nperiodic_dimensions ({self.nperiodic_dimensions}) does not match "
                    f"expected value of {sum(self.dimension_types)} from dimension_types "
                    f"({self.dimension_types})"
                )

        if self.lattice_vectors is not None:
            if self.dimension_types:
                for dim_type, vector in zip(self.dimension_types, self.lattice_vectors):
                    if None in vector and dim_type == Periodicity.PERIODIC.value:
                        raise ValueError(
                            f"Null entries in lattice vectors are only permitted when the "
                            "corresponding dimension type is "
                            f"{Periodicity.APERIODIC.value}. Here: dimension_types = "
                            f"{tuple(getattr(_, 'value', None) for _ in self.dimension_types)},"
                            f" lattice_vectors = {self.lattice_vectors}"
                        )

        return self

    @field_validator("lattice_vectors", mode="after")
    @classmethod
    def null_values_for_whole_vector(
        cls,
        value: None
        | (Annotated[list[Vector3D_unknown], Field(min_length=3, max_length=3)]),
    ) -> Annotated[list[Vector3D_unknown], Field(min_length=3, max_length=3)] | None:
        if value is None:
            return value

        for vector in value:
            if None in vector and any(isinstance(_, float) for _ in vector):
                raise ValueError(
                    "A lattice vector MUST be either all `null` or all numbers "
                    f"(vector: {vector}, all vectors: {value})"
                )
        return value

    @model_validator(mode="after")
    def validate_nsites(self) -> "StructureResourceAttributes":
        if self.nsites is None:
            return self

        if self.cartesian_site_positions and self.nsites != len(
            self.cartesian_site_positions
        ):
            raise ValueError(
                f"nsites (value: {self.nsites}) MUST equal length of "
                "cartesian_site_positions (value: "
                f"{len(self.cartesian_site_positions)})"
            )
        return self

    @model_validator(mode="after")
    def validate_species_at_sites(self) -> "StructureResourceAttributes":
        if self.species_at_sites is None:
            return self

        if self.nsites and len(self.species_at_sites) != self.nsites:
            raise ValueError(
                f"Number of species_at_sites (value: {len(self.species_at_sites)}) "
                f"MUST equal number of sites (value: {self.nsites})"
            )

        if self.species:
            all_species_names = {_.name for _ in self.species}

            for species_at_site in self.species_at_sites:
                if species_at_site not in all_species_names:
                    raise ValueError(
                        "species_at_sites MUST be represented by a species' name, "
                        f"but {species_at_site} was not found in the list of species "
                        f"names: {all_species_names}"
                    )

        return self

    @field_validator("species", mode="after")
    @classmethod
    def validate_species(cls, value: list[Species] | None) -> list[Species] | None:
        if value is None:
            return value

        all_species = [_.name for _ in value]
        unique_species = set(all_species)
        if len(all_species) != len(unique_species):
            raise ValueError(
                f"Species MUST be unique based on their 'name'. Found species names: {all_species}"
            )

        return value

    @model_validator(mode="after")
    def check_symmetry_operations(self) -> "StructureResourceAttributes":
        if self.nperiodic_dimensions == 0 and self.space_group_symmetry_operations_xyz:
            raise ValueError(
                "Non-periodic structures MUST NOT have space group symmetry operations."
            )

        if (
            self.space_group_symmetry_operations_xyz
            and "x,y,z" not in self.space_group_symmetry_operations_xyz
        ):
            raise ValueError(
                "The identity operation 'x,y,z' MUST be included in the space group symmetry operations, if provided."
            )

        return self

    @model_validator(mode="after")
    def validate_structure_features(self) -> "StructureResourceAttributes":
        if [
            StructureFeatures(value)
            for value in sorted(_.value for _ in self.structure_features)
        ] != self.structure_features:
            raise ValueError(
                "structure_features MUST be sorted alphabetically, structure_features: "
                f"{self.structure_features}"
            )

        # assemblies
        if self.assemblies is not None:
            if StructureFeatures.ASSEMBLIES not in self.structure_features:
                raise ValueError(
                    f"{StructureFeatures.ASSEMBLIES.value} MUST be present, since the "
                    "property of the same name is present"
                )
        elif StructureFeatures.ASSEMBLIES in self.structure_features:
            raise ValueError(
                f"{StructureFeatures.ASSEMBLIES.value} MUST NOT be present, "
                "since the property of the same name is not present"
            )

        if self.species:
            # disorder
            for species in self.species:
                if len(species.chemical_symbols) > 1:
                    if StructureFeatures.DISORDER not in self.structure_features:
                        raise ValueError(
                            f"{StructureFeatures.DISORDER.value} MUST be present when "
                            "any one entry in species has a chemical_symbols list "
                            "greater than one element"
                        )
                    break

            # site_attachments
            for species in self.species:
                # There is no need to also test "nattached",
                # since a Species validator makes sure either both are present or both are None.
                if species.attached is not None:
                    if (
                        StructureFeatures.SITE_ATTACHMENTS
                        not in self.structure_features
                    ):
                        raise ValueError(
                            f"{StructureFeatures.SITE_ATTACHMENTS.value} MUST be "
                            "present when any one entry in species includes attached "
                            "and nattached"
                        )
                    break
            else:
                if StructureFeatures.SITE_ATTACHMENTS in self.structure_features:
                    raise ValueError(
                        f"{StructureFeatures.SITE_ATTACHMENTS.value} MUST NOT be "
                        "present, since no species includes the attached and nattached"
                        " fields"
                    )

            # implicit_atoms
            for name in [_.name for _ in self.species]:
                if (
                    self.species_at_sites is not None
                    and name not in self.species_at_sites
                ):
                    if StructureFeatures.IMPLICIT_ATOMS not in self.structure_features:
                        raise ValueError(
                            f"{StructureFeatures.IMPLICIT_ATOMS.value} MUST be present"
                            " when any one entry in species is not represented in "
                            "species_at_sites"
                        )
                    break
            else:
                if StructureFeatures.IMPLICIT_ATOMS in self.structure_features:
                    raise ValueError(
                        f"{StructureFeatures.IMPLICIT_ATOMS.value} MUST NOT be "
                        "present, since all species are represented in species_at_sites"
                    )

        return self


class StructureResource(EntryResource):
    """Representing a structure."""

    type: Annotated[
        Literal["structures"],
        StrictField(
            description="""The name of the type of an entry.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

- **Examples**:
    - `"structures"`""",
            pattern="^structures$",
            support=SupportLevel.MUST,
            queryable=SupportLevel.MUST,
        ),
    ] = "structures"

    attributes: StructureResourceAttributes
