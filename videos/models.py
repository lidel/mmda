from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedArtistVideos(Document):
    """
    Contains artist related video meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

