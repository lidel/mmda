from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedArtist(Document):
    """
    Contains Artist related data fetched from various sources.
    """
    images      = DictProperty(default={})
    urls        = DictProperty(default={})
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

class CachedReleaseGroup(Document):
    """
    Contains Release Group related data fetched from various sources.
    """
    releases    = DictProperty(default={})
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

