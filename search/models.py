from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedSearchResult(Document):
    """
    CouchDB document that store search result for later use.
    """
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

