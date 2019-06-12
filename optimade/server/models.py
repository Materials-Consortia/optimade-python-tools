from datetime import datetime
from typing import Optional, Union, List, Dict

from pydantic import BaseModel, UrlStr, validator, ConstrainedInt, Schema


class Link(BaseModel):
    href: UrlStr
    meta: Optional[dict]


class Links(BaseModel):
    next: Optional[Union[UrlStr,Link]]
    base_url: Optional[Union[UrlStr,Link]]


class OptimadeResponseMetaQuery(BaseModel):
    representation: str

    @validator('representation')
    def representation_must_be_valid_url_with_base(cls, v):
        UrlStr(f'https://baseurl.net{v}')
        return v


class NonnegativeInt(ConstrainedInt):
    ge = 0


class Resource(BaseModel):
    id: str
    type: str


class EntryResourceAttributes(BaseModel):
    local_id: str
    last_modified: datetime
    immutable_id: Optional[str]


class EntryResource(Resource):
    attributes: EntryResourceAttributes


class StructureResourceAttributes(EntryResourceAttributes):
    elements: str = None
    nelements: int = None
    chemical_formula: str = None
    formula_prototype: str = None


class StructureResource(EntryResource):
    type = "structure"
    attributes: StructureResourceAttributes


class OptimadeResponseMeta(BaseModel):
    """
    A JSON API meta member that contains JSON API meta objects of non-standard meta-information.

    In addition to the required fields, it MAY contain

    - `data_available`: an integer containing the total number of data objects available in the database.
    - `last_id`: a string containing the last ID returned.
    - `response_message`: response string from the server.

    Other OPTIONAL additional information global to the query that is not specified in this document, MUST start with
    a database-provider-specific prefix
    """
    query: OptimadeResponseMetaQuery
    api_version: str = Schema(..., description="a string containing the version of the API implementation.")
    time_stamp: datetime
    data_returned: NonnegativeInt
    more_data_available: bool
    data_available: Optional[NonnegativeInt]
    last_id: Optional[str]
    response_message: Optional[str]

class OptimadeResponse1(BaseModel):
    links: Links
    meta: OptimadeResponseMeta
    data: Resource

class OptimadeResponseMany(BaseModel):
    links: Links
    meta: OptimadeResponseMeta
    data: List[Resource]

class ErrorSource(BaseModel):
     pointer: Optional[str]=Schema(..., description='a JSON Pointer [RFC6901] to the associated entity in the request document [e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].')
     parameter: Optional[str]=Schema(..., description='a string indicating which URI query parameter caused the error.')


class ErrorMsg(BaseModel):
    id: str=Schema(..., description="a unique identifier for this particular occurrence of the problem.")
    links: Dict[str, Union[str, Link]]=Schema(..., description="a list of links objects.")
    status: str=Schema(..., description="the HTTP status code applicable to this problem, expressed as a string value.")
    code: str=Schema(..., description="an application-specific error code, expressed as a string value.")
    title: str=Schema(..., description="a short, human-readable summary of the problem that SHOULD NOT change from occurrence to occurrence of the problem, except for purposes of localization.")
    detail: str=Schema(..., description="a human-readable explanation specific to this occurrence of the problem. Like title, this field’s value can be localized.")
    source: ErrorSource=Schema(..., description="an object containing references to the source of the error")
    meta: dict=Schema(..., description="a meta object containing non-standard meta-information about the error.")


class OptimadeResponseError(BaseModel):
    links: Optional[Links]
    meta: OptimadeResponseMeta
    errors: List[ErrorMsg]


class OptimadeStructureResponse1(OptimadeResponse1):
    data: StructureResource


class OptimadeStructureResponseMany(OptimadeResponseMany):
    data: List[StructureResource]


class BaseInfoAttributes(BaseModel):
    api_version: str
    available_api_versions: Dict[str, UrlStr]
    formats: List[str] = ["json"]
    entry_types_by_format: Dict[str, List[str]]
    available_endpoints: List[str] = ["structure", "all", "info"]


class BaseInfoResource(BaseModel):
    id: str = "/"
    type: str = "info"
    attributes: BaseInfoAttributes


class OptimadeInfoResponse(OptimadeResponse1):
    meta: Optional[OptimadeResponseMeta]
    data: BaseInfoResource


class EntryPropertyInfo(BaseModel):
    description: str
    unit: Optional[str]


class EntryInfoAttributes(BaseModel):
    description: str
    properties: Dict[str, EntryPropertyInfo]
    formats: List[str] = ["json"]
    output_fields_by_format: Dict[str, List[str]]


class EntryInfoResource(BaseModel):
    id: str
    type: str = "info"
    attributes: EntryInfoAttributes


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



