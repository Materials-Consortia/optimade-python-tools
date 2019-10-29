from configparser import ConfigParser
from pathlib import Path


config = ConfigParser()
config.read(Path(__file__).resolve().parent.parent.joinpath("config.ini"))
PROVIDER = config["DEFAULT"].get("PROVIDER")
PROVIDER_FIELDS = {field for field, _ in config["STRUCTURE"].items() if _ == ""}


class StructureMapper:
    aliases = tuple((PROVIDER + _, _) for _ in PROVIDER_FIELDS)
    aliases += (
        ("id", "task_id"),
        ("chemical_formula_descriptive", "pretty_formula"),
        ("chemical_formula_reduced", "pretty_formula"),
        ("chemical_formula_anonymous", "formula_anonymous"),
    )

    @classmethod
    def alias_for(cls, field):
        return dict(cls.aliases).get(field, field)

    @classmethod
    def map_back(cls, doc):
        if "_id" in doc:
            del doc["_id"]
        if "nsites" not in doc:
            doc["nsites"] = len(doc.get("cartesian_site_positions", []))
        # print(doc)
        mapping = ((real, alias) for alias, real in cls.aliases)
        newdoc = {}
        reals = {real for alias, real in cls.aliases}
        for k in doc:
            if k not in reals:
                newdoc[k] = doc[k]
        for real, alias in mapping:
            if real in doc:
                newdoc[alias] = doc[real]

        # print(newdoc)
        if "attributes" in newdoc:
            raise Exception("Will overwrite doc field!")
        newdoc["attributes"] = newdoc.copy()
        for k in {"id", "type"}:
            newdoc["attributes"].pop(k, None)
        for k in list(newdoc.keys()):
            if k not in ("id", "attributes"):
                del newdoc[k]
        newdoc["type"] = "structures"
        return newdoc
