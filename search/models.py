from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedSearchResult(Document, CachedDocument):
    """
    CouchDB document that store search result for later use.
    """
    cache_state = DictProperty(default={})

