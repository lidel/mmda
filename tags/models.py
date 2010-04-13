from couchdbkit.ext.django.schema import Document, DictProperty

class CachedTag(Document):
    """
    Contains tag related meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

