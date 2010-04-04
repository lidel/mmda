from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^artist/', include('mmda.artists.urls')),
    (r'^search/', include('mmda.search.urls'))
)
