# pylint: disable=no-self-argument,line-too-long,no-name-in-module
import warnings
from typing import List, Optional, Union, Any
from enum import IntEnum
from pydantic import BaseModel, root_validator, conlist

from optimade.models.entries import EntryResourceAttributes, EntryResource
from optimade.models.utils import (
    CHEMICAL_SYMBOLS,
    EXTRA_SYMBOLS,
    OptimadeField,
    StrictField,
    SupportLevel,
)
from optimade.server.warnings import MissingExpectedField
from optimade.models.structures import StructureAttributes

EXTENDED_CHEMICAL_SYMBOLS = set(CHEMICAL_SYMBOLS + EXTRA_SYMBOLS)

__all__ = (
    "Vector3D",
    "TrajectoryResourceAttributes",
    "AvailablePropertySubfields",
    "AvailablePropertyAttributes",
    "TrajectoryDataAttributes",
    "TrajectoryResource",
    "Periodicity",
)

# Use machine epsilon for single point floating precision
EPS = 2**-23

Vector3D = conlist(float, min_items=3, max_items=3)
Vector3D_unknown = conlist(Union[float, None], min_items=3, max_items=3)

CORRELATED_STRUCTURE_FIELDS = (
    {"cartesian_site_positions", "species_at_sites"},
    {"species_at_sites", "species"},
)

general_description_trajectory_field = """To define how this property is stored for each of the frames in the trajectory the following properties have been defined:
- **frame_serialization_format**:

  - **Description**: To improve the compactness of the data there are several ways to show to which frame a value belongs.
    This is specified by the :property:`frame_serialization_format`.
  - **Type**: string
  - **Requirements/Conventions**: This field MUST be present.
  - **Values**:

    - **constant**: The value of the property is constant and thus has the same value for each frame in the trajectory.
    - **explicit**: A value is given for each frame.
      The number of values MUST thus be equal to the number of frames and MUST be in the same order as the frames.
      If there is no value for a particular frame the value MUST be :val:`null`.
    - **linear**: The value is a linear function of the frame number.
      This function is defined by :property:`offset_linear` and :property:`step_size_linear`.
    - **explicit_regular_sparse**: The value is set every one per :property:`step_size_sparse` frames, with :property:`offset_sparse` as the first frame.
    - **explicit_custom_sparse**: A separate list with frame numbers is defined in the field :property:`sparse_frames` to indicate to which frame a value belongs.

- **offset_linear**:

  - **Description**: If :property:`frame_serialization_format` is set to :val:`"linear"` this property gives the value at frame 0.
  - **Type**: float
  - **Requirements/Conventions**: The value MAY be present when :property:`frame_serialization_format` is set to :val:`"linear"`, otherwise the value MUST NOT be present.
    The default value is 0.
  - **Examples**:

    - :val:`1.5`

- **step_size_linear**:

  - **Description**: If :property:`frame_serialization_format` is set to :val:`"linear"`, this value gives the change in the value of the property per unit of frame number.
    e.g. If at frame 3 the value of the property is 0.6 and :property:`step_size_linear` = 0.2 than at frame 4 the value of the property will be 0.8.
  - **Type**: float
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to "linear".
    Otherwise it MUST NOT be present.
  - **Examples**:

    - :val:`0.0005`

- **offset_sparse**:

  - **Description**: If :property:`frame_serialization_format` is set to :val:` "explicit_regular_sparse"` this property gives the frame number to which the first value belongs.
  - **Type**: integer
  - **Requirements/Conventions**: The value MAY be present when :property:`frame_serialization_format` is set to :val:`"explicit_regular_sparse"`, otherwise the value MUST NOT be present.
    The default value is 0.
  - **Examples**:

    - :val:`100`

- **step_size_sparse**:

  - **Description**: If :property:`frame_serialization_format` is set to :val:` "explicit_regular_sparse"`, this value indicates that every step_size_sparse frames a value is defined.
  - **Type**: integer
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to :val:`"explicit_regular_sparse"`.
    Otherwise it MUST NOT be present.
  - **Examples**:

    - :val:`100`

- **sparse_frames**:

  - **Description**: If :property:`frame_serialization_format` is set to :val:`"explicit_custom_sparse"`, this field holds the frames to which the values in the value field belong.
  - **Type**: List of integers
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to "explicit_custom_sparse".
    Otherwise it MUST NOT be present.
    The frame numbers in :property:`sparse_frames` MUST be in the same order as the values.
  - **Examples**:

    - :val:`[0,20,78,345]`


- **values**:- **Description**: The values belonging to this property.
    The format of this field depends on the property and on the :property:`frame_serialization_format` parameter.
  - **Type**: List of Any
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is not set to :val:`"linear"`.
    If a value has not been sampled for a particular frame the value should be set to :val:`null` at the highest possible nesting level.
    In case of `cartesian_site_positions`_, a site that has the value :val:`null` for the x,y and z coordinates means that the site is not in the simulation volume.
    This may be useful for grand canonical simulations where the number of particles in the simulation volume is not constant."""


class Periodicity(IntEnum):
    """Integer enumeration of dimension_types values"""

    APERIODIC = 0
    PERIODIC = 1


class AvailablePropertySubfields(BaseModel):
    frame_serialization_format: str = OptimadeField(
        ...,
        description="""To improve the compactness of the data there are several ways to show to which frame a value belongs.
    This is specified by the :property:`frame_serialization_format`.
  - **Type**: string
  - **Requirements/Conventions**: This field MUST be present.
  - **Values**:

    - **constant**: The value of the property is constant and thus has the same value for each frame in the trajectory.
    - **explicit**: A value is given for each frame.
      The number of values MUST thus be equal to the number of frames and MUST be in the same order as the frames.
      If there is no value for a particular frame the value MUST be :val:`null`.
    - **linear**: The value is a linear function of the frame number.
      This function is defined by :property:`offset_linear` and :property:`step_size_linear`.
    - **explicit_regular_sparse**: The value is set every one per :property:`step_size_sparse` frames, with :property:`offset_sparse` as the first frame.
    - **explicit_custom_sparse**: A separate list with frame numbers is defined in the field :property:`sparse_frames` to indicate to which frame a value belongs.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )
    nvalues: Optional[int] = OptimadeField(
        None,
        description="""This field gives the number of values for this property.
    - **Type**: integer
    - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to explicit, explicit_regular_sparse or explicit_custom_sparse.
    - **Examples**:
      - :val:`100`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class AvailablePropertyAttributes(BaseModel):
    cartesian_site_positions: Optional[AvailablePropertySubfields] = OptimadeField(
        None,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    lattice_vectors: Optional[AvailablePropertySubfields] = OptimadeField(
        None,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species: Optional[AvailablePropertySubfields] = OptimadeField(
        None,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    dimension_types: Optional[AvailablePropertySubfields] = OptimadeField(
        None,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species_at_sites: Optional[AvailablePropertySubfields] = OptimadeField(
        None,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    _exmpl_time: Optional[AvailablePropertySubfields] = OptimadeField(
        None,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class TrajectoryDataAttributes(AvailablePropertySubfields):
    # TODO Figure out why I need to comment out the support field for these optional properties to pass the validator.
    # storage_location: str = OptimadeField(
    #     ...,
    #     description="""The location where the data belonging to this property is stored. For now either 'mongo' or file.""",
    #     support=SupportLevel.MUST,
    #     queryable=SupportLevel.OPTIONAL,
    # )
    offset_linear: Optional[float] = OptimadeField(
        None,
        description="""If :property:`frame_serialization_format` is set to :val:`"linear"` this property gives the value at frame 0.
  - **Type**: float
  - **Requirements/Conventions**: The value MAY be present when :property:`frame_serialization_format` is set to :val:`"linear"`, otherwise the value MUST NOT be present.
    The default value is 0.
  - **Examples**:

    - :val:`1.5`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    step_size_linear: Optional[float] = OptimadeField(
        None,
        description="""If :property:`frame_serialization_format` is set to :val:`"linear"`, this value gives the change in the value of the property per unit of frame number.
    e.g. If at frame 3 the value of the property is 0.6 and :property:`step_size_linear` = 0.2 than at frame 4 the value of the property will be 0.8.
  - **Type**: float
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to "linear".
    Otherwise it MUST NOT be present.
  - **Examples**:

    - :val:`0.0005`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    offset_sparse: Optional[int] = OptimadeField(
        None,
        description="""If :property:`frame_serialization_format` is set to :val:` "explicit_regular_sparse"` this property gives the frame number to which the first value belongs.
  - **Type**: integer
  - **Requirements/Conventions**: The value MAY be present when :property:`frame_serialization_format` is set to :val:`"explicit_regular_sparse"`, otherwise the value MUST NOT be present.
    The default value is 0.
  - **Examples**:

    - :val:`100`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    step_size_sparse: Optional[int] = OptimadeField(
        None,
        description="""If :property:`frame_serialization_format` is set to :val:` "explicit_regular_sparse"`, this value indicates that every step_size_sparse frames a value is defined.
  - **Type**: integer
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to :val:`"explicit_regular_sparse"`.
    Otherwise it MUST NOT be present.
  - **Examples**:

    - :val:`100`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    sparse_frames: Optional[List[int]] = OptimadeField(
        None,
        description="""If :property:`frame_serialization_format` is set to :val:`"explicit_custom_sparse"`, this field holds the frames to which the values in the value field belong.
  - **Type**: List of integers
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to "explicit_custom_sparse".
    Otherwise it MUST NOT be present.
    The frame numbers in :property:`sparse_frames` MUST be in the same order as the values.
  - **Examples**:

    - :val:`[0,20,78,345]`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    values: Optional[List[Any]] = OptimadeField(
        None,
        description="""A list with the values for this property in the trajectory.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class TrajectoryResourceAttributes(EntryResourceAttributes):
    """This class contains the Field for the attributes used to represent a structure, e.g. unit cell, atoms, positions."""

    reference_structure: StructureAttributes = OptimadeField(
        ...,
        description="""This is an example of the structures that can be found in the trajectory.
  It can be used to select trajectories with queries and to give a quick visual impression of the structures in this trajectory.
- **Type**: dictionary
- **Requirements/Conventions**:

  - Each trajectory MUST have a :property:`reference_structure`.
  - This :property:`reference_structure` MAY be one of the frames from the trajectory, in that case the `reference_frame`_ field MUST specify which frame has been used.
  - Queries on the trajectories MUST be done on the information supplied in the :property:`reference_structure` when the queried property is in the :property:`reference_structure`.
    The subfields of the reference_structure MUST have the same queryability as in the `structures entries`_.
    For example, the query : http://example.com/optimade/v1/trajectories?filter=nelements=2 would use the `nelements`_ property within the reference_structure.

  - This reference frame has the same properties as the structure entries namely:

    - `elements`
    - `nelements`
    - `elements_ratios`
    - `chemical_formula_descriptive`
    - `chemical_formula_reduced`
    - `chemical_formula_hill`
    - `chemical_formula_anonymous`
    - `dimension_types`
    - `nperiodic_dimensions`
    - `lattice_vectors`
    - `cartesian_site_positions`
    - `nsites`
    - `species_at_sites`
    - `species`
    - `assemblies`
    - `structure_features`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    reference_frame: Optional[int] = OptimadeField(
        None,
        description="""The number of the frame at which the `reference_structure` was taken.
  The first frame is frame 0.
- **Type**: integer
- **Requirements/Conventions**: The value MUST be equal or larger than 0 and less than nframes.

  - **Support**: MUST be supported if the `reference_structure`_ is taken from the trajectory.
    If the `reference_structure`_ is not in the trajectory, the value MUST NOT be present.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators.

- **Examples**:

  - :val:`42`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    nframes: int = OptimadeField(
        ...,
        description="""The number of the frames in the trajectory.
- **Type**: integer
- **Requirements/Conventions**:

  - **Support**: MUST be supported by all implementations, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.
  - The integer value MUST be equal to the length of the trajectory, that is, the number of frames.
  - The integer MUST be a positive non-zero value.

- **Querying**:

  - A filter that matches trajectories that have exactly 100 frames:
    - :filter:`nframes=100`
  - A filter that matches trajectories that have between 100 and 1000 frames:
    - :filter:`nframes>=100 AND nframes<=1000`

- **Examples**:

  -   :val:`42`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    available_properties: AvailablePropertyAttributes = OptimadeField(
        ...,
        description="""A dictionary with an entry for each of the properties for which data is available in the trajectory.
  The key is the name of the property.
  The value is a dictionary containing information about which value belongs to which frame.
  This makes it easier for a client to estimate the amount of data a query returns.

  It is up to the server to decide which properties to share and there are no mandatory fields.
  When sharing `cartesian_site_positions`_ the `lattice_vectors`_, `species`_, `dimension_types`_ and `species_at_sites`_ MUST however be shared as well.


- **Type**: dictionary of dictionaries
- **Requirements/Conventions**:

  -   **Support**: MUST be supported by all implementations, i.e., MUST NOT be :val:`null`.
  -   **Query**: MUST be a queryable property with support for all mandatory filter features.

- **Sub dictionary fields**

  - **frame_serialization_format**

    -   **Description**: This property describes how the frames and the returned values of a property are related.
        For each :property:`frame_serialization_format` method there are additional fields that describe how the values belong to the frames.
        These fields should also be present here.
        A complete description of the :property:`frame_serialization_format` methods and the fields belonging to these methods can be found in the section: `Return Format for Trajectory Data`_

  - **nvalues**:

    - **Description**: This field gives the number of values for this property.
    - **Type**: integer
    - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to explicit, explicit_regular_sparse or explicit_custom_sparse.
    - **Examples**:

      - :val:`100`
      - **Examples**:

    .. code:: jsonc

         "available_properties": {
           "cartesian_site_positions": {
             "frame_serialization_format": "explicit",
             "nvalues": 1000
           },
           "lattice_vectors":{
             "frame_serialization_format": "constant",
           },
           "species":{
             "frame_serialization_format": "constant",
           },
           "dimension_types":{
             "frame_serialization_format": "constant",
           },
           "species_at_sites":{
             "frame_serialization_format": "constant",
           },
           "_exmpl_pressure":{
             "frame_serialization_format": "explicit_custom_sparse",
             "nvalues": 20
           }
           "_exmpl_temperature":{
             "frame_serialization_format": "explicit_regular_sparse",
             "step_size_sparse": 10
             "nvalues": 100
           }
         }""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )
    # _exmpl_hdf5file_path: Optional[str] = OptimadeField( # TODO: this field is now still visible in the retrieved data this is however not neccesary.
    #     None,
    #     description="""The path of the file in which the trajectory information is stored.""",  # TODO: Use pathlib for the file_path. This property probably does not need to be an OPTIMADE property because
    #     support=SupportLevel.OPTIONAL,
    #     queryable=SupportLevel.OPTIONAL,
    # )
    cartesian_site_positions: Optional[
        TrajectoryDataAttributes
    ] = OptimadeField(  # TODO It should be possible to get these fields from the strcutureattributes class.
        None,
        description="""Cartesian positions of each site in the structure. A site is usually used
    to describe positions of atoms; what atoms can be encountered at a given site is conveyed by the species_at_sites
    property, and the species themselves are described in the species property.
    Type: list of list of floats
Requirements/Conventions:
Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.
It MUST be a list of length equal to the number of sites in the structure, where every element is a list of the three Cartesian coordinates of a site expressed as float values in the unit angstrom (Å).
An entry MAY have multiple sites at the same Cartesian position (for a relevant use of this, see e.g., the property assemblies).
When sharing `cartesian_site_positions`_ the `lattice_vectors`_, `species`_, `dimension_types`_ and `species_at_sites`_ MUST however be shared as well.
Examples:
[[0,0,0],[0,0,2]] indicates a structure with two sites, one sitting at the origin and one along the (positive) z-axis, 2 Å away from the origin.
"""
        + general_description_trajectory_field,
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    lattice_vectors: Optional[TrajectoryDataAttributes] = OptimadeField(
        None,
        description="""The three lattice vectors in Cartesian coordinates, in ångström (Å).
Type: list of list of floats or unknown values.
Requirements/Conventions:
Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.
MUST be a list of three vectors a, b, and c, where each of the vectors MUST BE a list of the vector's coordinates along the x, y, and z Cartesian coordinates. (Therefore, the first index runs over the three lattice vectors and the second index runs over the x, y, z Cartesian coordinates).
For databases that do not define an absolute Cartesian system (e.g., only defining the length and angles between vectors), the first lattice vector SHOULD be set along x and the second on the xy-plane.
MUST always contain three vectors of three coordinates each, independently of the elements of property dimension_types. The vectors SHOULD by convention be chosen so the determinant of the lattice_vectors matrix is different from zero. The vectors in the non-periodic directions have no significance beyond fulfilling these requirements.
The coordinates of the lattice vectors of non-periodic dimensions (i.e., those dimensions for which dimension_types is 0) MAY be given as a list of all null values. If a lattice vector contains the value null, all coordinates of that lattice vector MUST be null.
Examples:
[[4.0,0.0,0.0],[0.0,4.0,0.0],[0.0,1.0,4.0]] represents a cell, where the first vector is (4, 0, 0), i.e., a vector aligned along the x axis of length 4 Å; the second vector is (0, 4, 0); and the third vector is (0, 1, 4)."""
        + general_description_trajectory_field,
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species: Optional[TrajectoryDataAttributes] = OptimadeField(
        None,
        description="""A list describing the species of the sites of this structure. Species can represent pure chemical elements, virtual-crystal atoms representing a statistical occupation of a given site by multiple chemical elements, and/or a location to which there are attached atoms, i.e., atoms whose precise location are unknown beyond that they are attached to that position (frequently used to indicate hydrogen atoms attached to another element, e.g., a carbon with three attached hydrogens might represent a methyl group, -CH3).
Type: list of dictionary with keys:

name: string (REQUIRED)
chemical_symbols: list of strings (REQUIRED)
concentration: list of float (REQUIRED)
attached: list of strings (OPTIONAL)
nattached: list of integers (OPTIONAL)
mass: list of floats (OPTIONAL)
original_name: string (OPTIONAL).
Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.
Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.
Each list member MUST be a dictionary with the following keys:

name: REQUIRED; gives the name of the species; the name value MUST be unique in the species list;
chemical_symbols: REQUIRED; MUST be a list of strings of all chemical elements composing this species. Each item of the list MUST be one of the following:

a valid chemical-element symbol, or
the special value "X" to represent a non-chemical element, or
the special value "vacancy" to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the concentration list, see below).
If any one entry in the species list has a chemical_symbols list that is longer than 1 element, the correct flag MUST be set in the list structure_features (see property structure_features).
concentration: REQUIRED; MUST be a list of floats, with same length as chemical_symbols. The numbers represent the relative concentration of the corresponding chemical symbol in this species. The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations 1/3 and 2/3, the concentration might look something like [0.33333333333, 0.66666666666]. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.
Note that concentrations are uncorrelated between different sites (even of the same species).
attached: OPTIONAL; if provided MUST be a list of length 1 or more of strings of chemical symbols for the elements attached to this site, or "X" for a non-chemical element.
nattached: OPTIONAL; if provided MUST be a list of length 1 or more of integers indicating the number of attached atoms of the kind specified in the value of the attached key.

The implementation MUST include either both or none of the attached and nattached keys, and if they are provided, they MUST be of the same length. Furthermore, if they are provided, the structure_features property MUST include the string site_attachments.
mass: OPTIONAL. If present MUST be a list of floats, with the same length as chemical_symbols, providing element masses expressed in a.m.u. Elements denoting vacancies MUST have masses equal to 0.
original_name: OPTIONAL. Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation. The main use of this field is for source databases that use species names, containing characters that are not allowed (see description of the list property species_at_sites).
For systems that have only species formed by a single chemical symbol, and that have at most one species per chemical symbol, SHOULD use the chemical symbol as species name (e.g., "Ti" for titanium, "O" for oxygen, etc.) However, note that this is OPTIONAL, and client implementations MUST NOT assume that the key corresponds to a chemical symbol, nor assume that if the species name is a valid chemical symbol, that it represents a species with that chemical symbol. This means that a species {"name": "C", "chemical_symbols": ["Ti"], "concentration": [1.0]} is valid and represents a titanium species (and not a carbon species).
It is NOT RECOMMENDED that a structure includes species that do not have at least one corresponding site.
Examples:

[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]: any site with this species is occupied by a Ti atom.
[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": [0.0, 137.327, 40.078]} ]: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability.
[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [12.0]} ]: any site with this species is occupied by a carbon isotope with mass 12.
[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [13.0]} ]: any site with this species is occupied by a carbon isotope with mass 13.
[ {"name": "CH3", "chemical_symbols": ["C"], "concentration": [1.0], "attached": ["H"], "nattached": [3]} ]: any site with this species is occupied by a methyl group, -CH3, which is represented without specifying precise positions of the hydrogen atoms.
"""
        + general_description_trajectory_field,
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    dimension_types: Optional[TrajectoryDataAttributes] = OptimadeField(
        None,
        description="""List of three integers. For each of the three directions indicated by the three lattice vectors (see property lattice_vectors), this list indicates if the direction is periodic (value 1) or non-periodic (value 0). Note: the elements in this list each refer to the direction of the corresponding entry in lattice_vectors and not the Cartesian x, y, z directions.
Type: list of integers.
Requirements/Conventions:
Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.
Query: Support for queries on this property is OPTIONAL.
MUST be a list of length 3.
Each integer element MUST assume only the value 0 or 1.
Examples:
For a molecule: [0, 0, 0]
For a wire along the direction specified by the third lattice vector: [0, 0, 1]
For a 2D surface/slab, periodic on the plane defined by the first and third lattice vectors: [1, 0, 1]
For a bulk 3D system: [1, 1, 1]"""
        + general_description_trajectory_field,
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species_at_sites: Optional[TrajectoryDataAttributes] = OptimadeField(
        None,
        description="""Name of the species at each site (where values for sites are specified with the same order of the property cartesian_site_positions). The properties of the species are found in the property species.
Type: list of strings.
Requirements/Conventions:
Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.
Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.
MUST have length equal to the number of sites in the structure (first dimension of the list property cartesian_site_positions).
Each species name mentioned in the species_at_sites list MUST be described in the list property species (i.e. for each value in the species_at_sites list there MUST exist exactly one dictionary in the species list with the name attribute equal to the corresponding species_at_sites value).
Each site MUST be associated only to a single species. Note: However, species can represent mixtures of atoms, and multiple species MAY be defined for the same chemical element. This latter case is useful when different atoms of the same type need to be grouped or distinguished, for instance in simulation codes to assign different initial spin states.
Examples:
["Ti","O2"] indicates that the first site is hosting a species labeled "Ti" and the second a species labeled "O2".
["Ac", "Ac", "Ag", "Ir"] indicating the first two sites contains the "Ac" species, while the third and fourth sites contain the "Ag" and "Ir" species, respectively."""
        + general_description_trajectory_field,
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    _exmpl_time: Optional[TrajectoryDataAttributes] = OptimadeField(
        None,
        description="""The time belonging to each frame""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
        unit="ps",
    )

    # TODO add more Trajectory specific validators

    @root_validator(pre=True)
    def warn_on_missing_correlated_fields(
        cls, values
    ):  # TODO make better system for checking required sets of properties
        """Emit warnings if a field takes a null value when a value
        was expected based on the value/nullity of another field.
        """
        accumulated_warnings = []
        for field_set in CORRELATED_STRUCTURE_FIELDS:
            missing_fields = {f for f in field_set if values.get(f) is None}
            if missing_fields and len(missing_fields) != len(field_set):
                accumulated_warnings += [
                    f"Trajectories with values {values} is missing fields {missing_fields} which are required if {field_set - missing_fields} are present."
                ]
        for warn in accumulated_warnings:
            warnings.warn(warn, MissingExpectedField)

        return values


class TrajectoryResource(EntryResource):
    """Representing a trajectory."""

    type: str = StrictField(
        "trajectories",
        const="trajectories",
        description="""The name of the type of an entry.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

- **Examples**:
    - `"trajectories"`""",
        pattern="^trajectories$",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    attributes: TrajectoryResourceAttributes
