from couchdbkit.ext.django.schema import Document, DictProperty

class CachedArtistVideos(Document):
    """
    Contains artist related video meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

