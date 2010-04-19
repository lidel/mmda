from django.conf.urls.defaults import *
from mmda.engine.feeds import ArtistNewsFeed

feeds  = {
    'artist': ArtistNewsFeed,
}

urlpatterns = patterns('',
    (r'^artist/', include('mmda.pictures.urls')),
    (r'^artist/', include('mmda.videos.urls')),
    (r'^artist/', include('mmda.news.urls')),
    (r'^artist/', include('mmda.artists.urls')),
    (r'^tag/', include('mmda.tags.urls')),
    (r'^search/', include('mmda.search.urls')),
    (r'^(?P<url>.+)/feed/$','django.contrib.syndication.views.feed', {'feed_dict': feeds})
    #(r'^feed/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds})

)
