from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedArtistPictures(Document):
    """
    Contains artist related picture meta-data fetched from various sources.
    """
    cache_state = DictProperty(default={})

