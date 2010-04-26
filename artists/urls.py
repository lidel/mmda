from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.artists.views',
    url(r'^$', 'index', name='welcome-page'),
    url(r'^(?P<uri_artist>\S+)/release/(?P<uri_release>\S+)/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_release', name='show-release'),
    url(r'^(?P<uri_artist>\S+)/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_artist', name='show-artist'),
    url(r'^(?P<uri_artist>\S+)/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/refresh/$', 'show_artist_refresh', name='show-artist-refresh'),
)
urlpatterns += patterns('mmda.search.views',
   (r'^\S+/release/(?P<query_string>\S+)/$', 'create_search_result', {'query_type':'release'}),
   (r'^(?P<query_string>\S+)/$', 'create_search_result', {'query_type':'artist'}),
)
