# pylint: disable=no-self-argument,line-too-long,no-name-in-module
import warnings
from typing import List, Optional, Union, Any
from enum import IntEnum
from pydantic import BaseModel, validator, root_validator, conlist

from optimade.models.entries import EntryResourceAttributes, EntryResource
from optimade.models.utils import (
    CHEMICAL_SYMBOLS,
    EXTRA_SYMBOLS,
    OptimadeField,
    StrictField,
    SupportLevel,
)
from optimade.server.warnings import MissingExpectedField
from optimade.models.structures import (
    StructureResourceAttributes,
    CORRELATED_STRUCTURE_FIELDS,
)


EXTENDED_CHEMICAL_SYMBOLS = set(CHEMICAL_SYMBOLS + EXTRA_SYMBOLS)

__all__ = (
    "Vector3D",
    "TrajectoryResourceAttributes",
    "TrajectoryResource",
    "Periodicity",
)

# Use machine epsilon for single point floating precision
EPS = 2**-23

Vector3D = conlist(float, min_items=3, max_items=3)
Vector3D_unknown = conlist(Union[float, None], min_items=3, max_items=3)


class Periodicity(IntEnum):
    """Integer enumeration of dimension_types values"""

    APERIODIC = 0
    PERIODIC = 1


class ReferenceStructure(StructureResourceAttributes):
    """This class contains the reference structure.
    This reference structure is used to process queries on the trajectories without having to access the rest of the
    trajectory data. At the moment"""

    pass


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
    nvalues: int = OptimadeField(
        ...,
        description="""This field gives the number of values for this property.
    - **Type**: integer
    - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to explicit, explicit_regular_sparse or explicit_custom_sparse.
    - **Examples**:
      - :val:`100`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class AvailablePropertyAttributes(BaseModel):
    cartesian_site_positions: AvailablePropertySubfields = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    lattice_vectors: AvailablePropertySubfields = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species: AvailablePropertySubfields = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    dimension_types: AvailablePropertySubfields = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species_at_sites: AvailablePropertySubfields = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    _exmpl_time: AvailablePropertySubfields = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class TrajectoryDataAttributes(AvailablePropertySubfields):
    storage_location: str = OptimadeField(
        ...,
        description="""The location where the data belonging to this property is stored. For now either 'mongo' or file.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )
    offset_linear: Optional[float] = OptimadeField(
        ...,
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
        ...,
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
        ...,
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
        ...,
        description="""If :property:`frame_serialization_format` is set to :val:` "explicit_regular_sparse"`, this value indicates that every step_size_sparse frames a value is defined.
  - **Type**: integer
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to :val:`"explicit_regular_sparse"`.
    Otherwise it MUST NOT be present.
  - **Examples**:

    - :val:`100`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )
    sparse_frames: Optional[List[int]] = OptimadeField(
        ...,
        description="""If :property:`frame_serialization_format` is set to :val:`"explicit_custom_sparse"`, this field holds the frames to which the values in the value field belong.
  - **Type**: List of integers
  - **Requirements/Conventions**: The value MUST be present when :property:`frame_serialization_format` is set to "explicit_custom_sparse".
    Otherwise it MUST NOT be present.
    The frame numbers in :property:`sparse_frames` MUST be in the same order as the values.
  - **Examples**:

    - :val:`[0,20,78,345]`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    values: Optional[List[Any]] = OptimadeField(
        ...,
        description="""A list with the values for this property in the trajectory.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class TrajectoryResourceAttributes(EntryResourceAttributes):
    """This class contains the Field for the attributes used to represent a structure, e.g. unit cell, atoms, positions."""

    reference_structure: ReferenceStructure = OptimadeField(
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
        ...,
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
    _exmpl_file_path: Optional[str] = OptimadeField(
        ...,
        description="""The path of the file in which the trajectory information is stored.""",  # TODO: Use pathlib for the file_path. This property probably does not need to be an OPTIMADE property because
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    cartesian_site_positions: TrajectoryDataAttributes = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    lattice_vectors: TrajectoryDataAttributes = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species: TrajectoryDataAttributes = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    dimension_types: TrajectoryDataAttributes = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    species_at_sites: TrajectoryDataAttributes = OptimadeField(
        ...,
        description="""""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )
    _exmpl_time: TrajectoryDataAttributes = OptimadeField(
        ...,
        description="""The time belonging to each frame""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
        unit="ps",
    )

    class Config:
        def schema_extra(schema, model):
            """Two things need to be added to the schema:

            1. Constrained types in pydantic do not currently play nicely with
            "Required Optional" fields, i.e. fields must be specified but can be null.
            The two contrained list fields, `dimension_types` and `lattice_vectors`,
            are OPTIMADE 'SHOULD' fields, which means that they are allowed to be null.

            2. All OPTIMADE 'SHOULD' fields are allowed to be null, so we manually set them
            to be `nullable` according to the OpenAPI definition.

            """
            schema["required"].insert(7, "dimension_types")
            schema["required"].insert(9, "lattice_vectors")

            nullable_props = (
                prop
                for prop in schema["required"]
                if schema["properties"][prop].get("support") == SupportLevel.SHOULD
            )
            for prop in nullable_props:
                schema["properties"][prop]["nullable"] = True

    # TODO add more Trajectory specific validators

    @root_validator(pre=True)
    def warn_on_missing_correlated_fields(cls, values):
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

    @validator("lattice_vectors", always=True)
    def required_if_dimension_types_has_one(cls, v, values):
        if v is None:
            return v

        if values.get("dimension_types"):
            for dim_type, vector in zip(values.get("dimension_types", (None,) * 3), v):
                if None in vector and dim_type == Periodicity.PERIODIC.value:
                    raise ValueError(
                        f"Null entries in lattice vectors are only permitted when the corresponding dimension type is {Periodicity.APERIODIC.value}. "
                        f"Here: dimension_types = {tuple(getattr(_, 'value', None) for _ in values.get('dimension_types', []))}, lattice_vectors = {v}"
                    )
        return v

    @validator("lattice_vectors")
    def null_values_for_whole_vector(cls, v):
        if v is None:
            return v

        for vector in v:
            if None in vector and any((isinstance(_, float) for _ in vector)):
                raise ValueError(
                    f"A lattice vector MUST be either all `null` or all numbers (vector: {vector}, all vectors: {v})"
                )
        return v

    @validator("species_at_sites")
    def validate_species_at_sites(cls, v, values):
        if v is None:
            return v

        if values.get("nsites") and len(v) != values.get("nsites"):
            raise ValueError(
                f"Number of species_at_sites (value: {len(v)}) MUST equal number of sites "
                f"(value: {values.get('nsites', 'Not specified')})"
            )
        if values.get("species"):
            all_species_names = {
                getattr(_, "name", None) for _ in values.get("species", [{}])
            }
            all_species_names -= {None}
            for value in v:
                if value not in all_species_names:
                    raise ValueError(
                        "species_at_sites MUST be represented by a species' name, "
                        f"but {value} was not found in the list of species names: {all_species_names}"
                    )
        return v

    @validator("species")
    def validate_species(cls, v):
        if v is None:
            return v

        all_species = [_.name for _ in v]
        unique_species = set(all_species)
        if len(all_species) != len(unique_species):
            raise ValueError(
                f"Species MUST be unique based on their 'name'. Found species names: {all_species}"
            )

        return v


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
