from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.artists.views',
    url(r'^$', 'index', name='welcome-page'),
    url(r'^(?P<uri_artist>\S+)/release/(?P<uri_release>\S+)/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_release', name='show-release'),
    url(r'^(?P<uri_artist>\S+)/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_artist', name='show-artist')
)
