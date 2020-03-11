from optimade.server.routers.links import links_coll
from optimade.server.routers.references import references_coll
from optimade.server.routers.structures import structures_coll

ENTRY_COLLECTIONS = {
    "links": links_coll,
    "references": references_coll,
    "structures": structures_coll,
}
