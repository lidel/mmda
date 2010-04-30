from django.conf.urls.defaults import *
from mmda.engine.feeds import ArtistNewsFeed
from django.conf import settings

feeds  = {
    'artist': ArtistNewsFeed,
}

urlpatterns = patterns('',
    (r'^artist/', include('mmda.pictures.urls')),
    (r'^artist/', include('mmda.videos.urls')),
    (r'^artist/', include('mmda.news.urls')),
    (r'^(?P<url>.+)/feed/$','django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^artist/', include('mmda.artists.urls')),
    (r'^tag/', include('mmda.tags.urls')),
    (r'^search/', include('mmda.search.urls')),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_DOC_ROOT, 'show_indexes': True}),

)
