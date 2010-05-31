from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.search.views',
    (r'^$', 'create_search_result'),
    url(r'^(?P<query_type>\S+)/(?P<query_string>[^/]+)/(?P<query_id>\w{40})/$', 'show_search_result', name='show-search-result'),
    url(r'^(?P<query_type>\S+)/(?P<query_string>[^/]+)/$', 'create_search_result', name='create-search-result')
    #url(r'^(?P<query_id>\w{40})/$', 'show_search_result', name='show-search-result-plain')
)
