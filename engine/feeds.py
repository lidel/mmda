# -*- coding: utf-8
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.utils.feedgenerator import Atom1Feed
from mmda.engine.artist import get_basic_artist
from mmda.engine.news import get_populated_artist_news
from mmda.artists.templatetags.release_helpers import slugify2, iso2date
from django.core.urlresolvers import reverse

from django.core.cache import cache


ITEMS_LIMIT = 30
# TODO: language awareness?

class ArtistNewsFeed(Feed):
    """
    Atom feed generator, with news stream for every artist.
    """

    news_sources = []
    feed_type = Atom1Feed
    title_template = 'feeds/artist_news/title.html'
    description_template = 'feeds/artist_news/description.html'


    def get_object(self, bits):
        try:
            # bits =  "uri_artist/news/mbid/"
            mbid = bits[2]
            artist = get_basic_artist(mbid)
            self.news_stream, self.news_sources = get_populated_artist_news(artist)
        except:
            raise FeedDoesNotExist
        else:
            return artist

    def title(self, artist):
        return u"%s – artist news stream at %s" % (artist.name, 'TODO')

    def subtitle(self):
        if self.news_sources:
            return "News fetched from: %s" % ', '.join([src['name'] for src in self.news_sources])
        else:
            return 'There are no news sources for this artist at this time, but as soon they will be added this feed will include them.'

    def link(self, artist):
        return reverse('show-artist-news', args=(slugify2(artist.name),'0cd12ab3-9628-45ef-a97b-ff18624f14a0')) # TODO? wtf

    def categories(self, artist):
        return ('music', artist.name)

    def items(self):
        return self.news_stream[:ITEMS_LIMIT]

    def item_link(self, item):
        return item['url']

    def item_pubdate(self, item):
        return iso2date(item['date'])
