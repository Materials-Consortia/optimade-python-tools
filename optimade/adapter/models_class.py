class Structure():
    def __init__(self, **kwargs):
        content = kwargs['param']
        self.id = content.get('material_id')
        self.elements = content.get('elements')
        self.nelements = content.get('nelements')
        self.pretty_formula = content.get('pretty_formula')
        self.formula_anonymous = content.get('formula_anonymous')

class Data():
    def __init__(self, id, structures):
        self.id = id
        self.structures = structures

class Links():
    def __init__(self, next, base_url):
        self.next = next
        self.base_url = base_url

class Meta():
    def __init__(self,
                query, # must be a dictionary with "representation": "/structures/?filter=a=1 AND b=2",
                api_version,
                time_stamp,
                data_returned,
                more_data_available,
                data_available=None, # optional
                last_id=None, # optional
                response_message=None #optional
                ):
        # TODO: check each type of each attribute based on the specification
        self.query = query
        self.api_version = api_version
        self.time_stamp = time_stamp
        self.data_returned = data_returned
        self.more_data_available = more_data_available
        self.last_id = last_id
        self.response_message = response_message

class Response():
    def __init__(self, links, meta, data):
        self.links = links
        self.meta = meta
        self.data = data
