from couchdbkit.ext.django.schema import Document, DictProperty

class CachedArtist(Document):
    """
    Contains artist related data fetched from various sources.
    """
    images      = DictProperty(default={})
    urls        = DictProperty(default={})
    cache_state = DictProperty(default={})

class CachedReleaseGroup(Document):
    """
    Contains release group related data fetched from various sources.
    """
    releases    = DictProperty(default={})
    cache_state = DictProperty(default={})

