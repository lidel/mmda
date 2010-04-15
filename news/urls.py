from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.news.views',
    url(r'^(?P<uri_artist>\S+)/news/(?P<mbid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'show_artist_news', name='show-artist-news')
)
