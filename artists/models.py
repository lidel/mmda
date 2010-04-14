from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedArtist(Document, CachedDocument):
    """
    Contains artist related data fetched from various sources.
    """
    images      = DictProperty(default={})
    urls        = DictProperty(default={})
    cache_state = DictProperty(default={})

class CachedReleaseGroup(Document, CachedDocument):
    """
    Contains release group related data fetched from various sources.
    """
    releases    = DictProperty(default={})
    cache_state = DictProperty(default={})

