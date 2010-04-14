from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedArtistVideos(Document, CachedDocument):
    """
    Contains artist related video meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

