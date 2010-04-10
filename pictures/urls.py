from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.pictures.views',
    url(r'^(?P<uri_artist>\S+)/pictures/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_artist_pictures', name='show-artist-pictures')
)
