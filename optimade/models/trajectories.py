# pylint: disable=no-self-argument,line-too-long,no-name-in-module
# import warnings
from typing import Optional

from pydantic import validator

from optimade.models.entries import EntryResource, EntryResourceAttributes
from optimade.models.structures import StructureAttributes

# from optimade.server.warnings import MissingExpectedField
from optimade.models.utils import (
    CHEMICAL_SYMBOLS,
    EXTRA_SYMBOLS,
    OptimadeField,
    StrictField,
    SupportLevel,
)

EXTENDED_CHEMICAL_SYMBOLS = set(CHEMICAL_SYMBOLS + EXTRA_SYMBOLS)

__all__ = (
    "TrajectoryResourceAttributes",
    "TrajectoryResource",
)

CORRELATED_TRAJECTORY_FIELDS = (
    {"cartesian_site_positions", "species_at_sites"},
    {"species_at_sites", "species"},
)


class TrajectoryResourceAttributes(EntryResourceAttributes, StructureAttributes):
    """This class contains the Field for the attributes used to represent a trajectory."""

    # todo get a better idea of how to inherrit from the Structure attributes while also allowing them to be list of fields as would be expected for a trajectory.

    reference_frames: Optional[int] = OptimadeField(
        None,
        description="""The indexes of a set of frames that give a good but very brief overview of the trajectory.
  The first frame could for example be a starting configuration, the second a transition state and the third the final state.
- **Type**: list of integers
- **Requirements/Conventions**: The values MUST be larger than or equal to 0 and less than nframes.

  - **Support**: OPTIONAL support in implementations, i.e., MAY be :val:`null`.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators.

- **Examples**:

  - :val:`[0, 397, 1000]`

 """,
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    @validator("reference_frames", each_item=True)
    def validate_reference_frames(cls, reference_frame):
        if reference_frame < 0:
            raise ValueError(
                f"All values in reference_frames have to positive integers. {reference_frame} is not a positive integer."
            )
        return reference_frame

    nframes: int = OptimadeField(
        ...,
        description=""" The number of frames in the trajectory as exposed by the API.
  This value may deviate from the number of steps used to calculate the trajectory.
  E.g., for a 10 ps simulation with calculation steps of 1 fs where data is stored once every 50 fs, nframes = 200.
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

  -   :val:`42`
""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    @validator("nframes")
    def validate_nframes(cls, nframes):
        if nframes < 0:
            raise ValueError("nframes must be a positive integer.")
        return nframes


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
