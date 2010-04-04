from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.search.views',
    (r'^$', 'create_search'),
    url(r'^(?P<query_id>\w{40})/$', 'show_search_result', name='show-search-result')
)
