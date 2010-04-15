from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedNewsItem(Document, CachedDocument):
    """
    Contains news item fetched from various sources.
    """
    cache_state = DictProperty(default={})

