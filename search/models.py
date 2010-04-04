from couchdbkit.ext.django.schema import Document, DictProperty
from datetime import datetime

class CachedSearchResult(Document):
    cache_state = DictProperty(default={"mb":[0,datetime.utcnow()]})

