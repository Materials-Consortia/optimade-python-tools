from optimade.server.models.entries import EntryResourceAttributes, EntryResource
from pydantic import Schema, constr, confloat
from typing import List


class StructureResourceAttributes(EntryResourceAttributes):
    elements: str = Schema(..., description="Names of elements found in the structure as a list of strings.")
    nelements: int = Schema(..., description="Number of elements found in a structure.")
    chemical_formula: str = Schema(..., description="""The chemical formula for a structure.

    * **Requirements/Conventions**:
     * The formula MUST be **reduced**.
     * Element names MUST be with proper capitalization (e.g., "Si", not "SI" for "silicon").
     * The order in which elements are specified SHOULD NOT be significant (e.g., "O2Si" is equivalent to "SiO2").
     * No spaces or separators are allowed.
     """)
    formula_prototype: str = Schema(...,description="The formula prototype obtained by sorting elements by the occurrence number in the reduced chemical formula and replacing them with subsequent alphabet letters A, B, C, and so on.")
    dimension_types: List[int, constr(max_length=3,min_length=3)] = Schema(..., description="""
    * **Requirements/Conventions**:
      * This property is REQUIRED, except when [6.2.5. `dimension_types`](#h.6.2.5) is equal to
        `[0, 0, 0]` (in this case it is OPTIONAL).
      * It MUST be a list of three vectors *a*, *b*, and *c*, where each of the vectors MUST BE a list of
        the vector's coordinates along the x, y, and z Cartesian coordinates. (Therefore, the first index
        runs over the three lattice vectors and the second index runs over the x, y, z Cartesian
        coordinates).
      * For databases that do not define an absolute Cartesian system (e.g., only defining the length and
        angles between vectors), the first lattice vector SHOULD be set along `x` and the second on the `xy`
        plane.
      * This property MUST be an array of dimensions 3 times 3 regardless of the elements of
        [6.2.5. `dimension_types`](#h.6.2.5). The vectors SHOULD by convention be chosen so the determinant
        of the `lattice_vectors` matrix is different from zero. The vectors in the non-periodic directions
        have no significance beyond fulfilling these requirements.
    * **Examples**:
      * `[[4.,0.,0.],[0.,4.,0.],[0.,1.,4.]]` represents a cell, where the first vector is
        `(4, 0, 0)`, i.e., a vector aligned along the `x` axis of length 4 Å; the second vector is
        `(0, 4, 0)`; and the third vector is `(0, 1, 4)`.
    """)

def list_length_validator(v: Any) -> List[Any]:
    if isinstance(v, list):
        return v
    elif sequence_like(v):
        return list(v)
    else:
        raise errors.ListError()



class StructureResource(EntryResource):
    """Representing a sturcture."""
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

    list_fields = (
        "elements",
    )

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
