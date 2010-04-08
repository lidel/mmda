from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedArtist(Document):
    images      = DictProperty(default={})
    urls        = DictProperty(default={})
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

class CachedReleaseGroup(Document):
    releases    = DictProperty(default={})
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

