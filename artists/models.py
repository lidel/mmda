from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedArtist(Document):
    """
    Contains artist related data fetched from various sources.
    """
    images      = DictProperty(default={})
    urls        = DictProperty(default={})
    # TODO: remove datetime from model (all models)
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

class CachedReleaseGroup(Document):
    """
    Contains release group related data fetched from various sources.
    """
    releases    = DictProperty(default={})
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

