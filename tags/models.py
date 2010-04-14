from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedTag(Document, CachedDocument):
    """
    Contains tag related meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

