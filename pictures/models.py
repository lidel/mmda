from couchdbkit.ext.django.schema import Document, DictProperty
from mmda.engine.cache import CachedDocument

class CachedArtistPictures(Document, CachedDocument):
    """
    Contains artist related picture meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

