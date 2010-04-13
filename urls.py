from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^artist/', include('mmda.pictures.urls')),
    (r'^artist/', include('mmda.videos.urls')),
    (r'^artist/', include('mmda.artists.urls')),
    (r'^tag/', include('mmda.tags.urls')),
    (r'^search/', include('mmda.search.urls'))
)
