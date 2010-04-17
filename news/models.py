from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedArtistNews(Document, CachedDocument):
    """
    Contains news about an artist fetched from various sources.
    """
    sources     = DictProperty(default={})
    cache_state = DictProperty(default={})

