from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.videos.views',
    url(r'^(?P<uri_artist>\S+)/videos/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_artist_videos', name='show-artist-videos')
)
