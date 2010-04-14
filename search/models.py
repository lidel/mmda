from couchdbkit.ext.django.schema import Document, DictProperty

class CachedSearchResult(Document):
    """
    CouchDB document that store search result for later use.
    """
    cache_state = DictProperty(default={})

