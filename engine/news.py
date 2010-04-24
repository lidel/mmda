# -*- coding: utf-8
from django.conf import settings
from django.utils.html  import strip_tags
from couchdbkit.ext.django.loading import get_db
from mmda.engine.utils  import mmda_logger
from mmda.engine.future import Future, timeout
from mmda.news.models import CachedArtistNews

import feedparser
import re
import urllib2
import urlparse

from operator import itemgetter

from datetime import datetime
from time import mktime
from sgmllib import SGMLParser

# MMDA is kind to introduce itself
feedparser.USER_AGENT = settings.USER_AGENT
HTTP_OPENER = urllib2.build_opener()
HTTP_OPENER.addheaders = [('User-agent', settings.USER_AGENT)]

BANNED_DOMAINS = ('twitter.com',)
LOOK_FOR_FEEDS = ('Blog','OfficialHomepage','Fanpage')

SEARCH_TIMEOUT  = 5 # seconds
FEED_CACHE = 86400 # = 1 day
SMART_FEED_CACHE = 900 # = 15 minutes

def get_populated_artist_news(artist):
    """
    Return populated object required by mmda.news.show_tag

    Designed to be stored in database only when populated by anything.

    @param artist: a CachedArtist object

    @return: a CachedArtistNews object
    """
    news = CachedArtistNews.get_or_create(artist.get_id)
    news = populate_artist_news(news, artist)
    news.save_any_changes()

    # neat trick with high unicode character and lexical sorting
    view = get_db('news').view('news/artist_news', startkey=[artist.get_id,u'\uFFF0'], endkey=[artist.get_id], descending=True)

    news_stream  = [group['value'] for group in view.all()]
    news_sources = [{'name':src['name'], 'url':src['url']} for url,src in news.sources.iteritems()]

    return (news_stream, news_sources)

def populate_artist_news(news, artist):

    # TODO: add condition that search for new feeds each 7 days?
    if news.sources:
        mmda_logger('news','present','cached',len(news.sources.keys()))
        """
            Sad story about ETag and Last-Modified Headers:

            SOME SITES JUST DON'T GIVE A DAMN.

            The End.

            Example:
                myspace feeds have no etag or L-M headers (17/Apr/2010)

            That is why MMDA uses 'cache' field to limit number
            of HTTP requests to such handicapped feeds separately

            reference: http://www.feedparser.org/docs/http-etag.html
        """
        now = datetime.utcnow()
        pending_sources = []

        for source_url in  news.sources.keys():
            source          = news.sources[source_url]
            etag            = source['etag']                    if source.has_key('etag')     else None
            last_modified   = source['modified'].utctimetuple() if source.has_key('modified') else None
            feed_is_smart   = etag or last_modified
            cache_time      = (now - source['cache']).seconds

            if (feed_is_smart and cache_time > SMART_FEED_CACHE) or cache_time > FEED_CACHE:
                pending_sources.append((source_url, etag, last_modified))
    else:
        # if there are no cached feeds
        pending_sources = _get_news_sources(artist)

    if pending_sources:

        try:
            t = mmda_logger('news','request','to check',len(pending_sources))
            future_calls = [Future(_get_fetched_and_parsed_feed,source) for source in pending_sources]
            fetched_feeds = [future_obj() for future_obj in future_calls if timeout(future_obj,t=20)]

        except Exception, e:
            mmda_logger('feed-fetch','ERROR',e)

        else:
            for feed in fetched_feeds:
                try:

                    if feed.status == 304:
                        mmda_logger('news','present','no updates',feed.href)
                        news.sources[feed.href]['cache'] = datetime.utcnow()
                        news.changes_present = True
                        continue
                    elif feed.status == 404:
                        mmda_logger('news','present','404',feed.href)
                        del news.sources[feed.href]
                    else:
                        feed_src = urlparse.urlsplit(feed.feed.link).netloc.replace('www.','')
                        mmda_logger('news','present','fetched',feed_src)

                    feed_entries = [{
                        'title':    e.title.strip() if e.has_key('title') else None,
                        'summary':  e.summary if e.has_key('summary') else None,
                        'date':     datetime(*e.updated_parsed[0:6]),
                        'url':      e.link
                        } for e in feed.entries]

                    news_source = {
                            'url':  feed.feed.link,
                            'name': feed_src,
                            'items':feed_entries,
                            'cache':datetime.utcnow()
                            }
                    if feed.has_key('modified') and feed.modified:
                        news_source['modified'] = datetime(*feed.modified[0:6])
                    if feed.has_key('etag') and feed.etag:
                        news_source['etag'] = feed.etag

                except Exception, e:
                    # some feeds may be badly formatted, sometimes FeedFinder may fail
                    # some myspace feeds have no entries...  trying
                    # to predict all possible failures is pointless.
                    # in such cases mmda just jumps to the next feed
                    mmda_logger('feed-parse','ERROR',e)
                    continue
                else:
                    news.sources[feed.href] = news_source
                    news.changes_present = True

            mmda_logger('news','result','got results',len(pending_sources),t)

    # TODO: move news sort to  view?
    #decorated = [(entry["date"], entry) for entry in entries]
    #decorated.sort()
    #decorated.reverse() # for most recent entries first
    #sorted = [entry for (date,entry) in decorated]
    return news


def _get_fetched_and_parsed_feed(source):
    """
    Return parsed feed from a source tuple.

    @param source: a tuple with feed url and optional etag/last-modified values

    @return: a feed object
    """
    source_url, etag, modified = source

    try:
        feed = feedparser.parse(source_url, etag=etag, modified=modified)
    except:
        return None
    else:
        return feed

class FeedFinder(SGMLParser):
    """
    Tool that finds if there is a RSS/Atom feed available for supplied website.

    _Strongly_ inspired and based on autorss.py by Mark Pilgrim:
    http://diveintomark.org/archives/2002/05/31/rss_autodiscovery_in_python
    """
    BUFFERSIZE = 1024

    def reset(self):
        SGMLParser.reset(self)
        self.href = ''

    def do_link(self, attrs):
        if not ('rel', 'alternate') in attrs: return
        # dont care if it is RSS or Atom since feedparser can parse them both
        if not (('type', 'application/rss+xml') in attrs or ('type', 'application/atom+xml') in attrs): return
        hreflist = [e[1] for e in attrs if e[0]=='href']
        if hreflist:
            # pick the first one - we don't want duplicates anyway
            self.href = hreflist[0]
        self.setnomoretags()

    def end_head(self, attrs):
        self.setnomoretags()
    start_body = end_head


def _get_feed_link_for(url):
    """
    Return feed url of the site specified by URL.

    Be smart, and fetch only head of a HTML file.

    @param url: a string with URL of a HTML page

    @return: a string with URL of RSS or Atom feed
    """
    try:
        feed_src = urlparse.urlsplit(url).netloc.replace('www.','')
        if feed_src in BANNED_DOMAINS:
            raise Exception
        # TODO: handle 301, 302 redirections
        usock = HTTP_OPENER.open(url, timeout=SEARCH_TIMEOUT)
        parser = FeedFinder()
        while 1:
            buffer = usock.read(parser.BUFFERSIZE)
            parser.feed(buffer)
            if parser.nomoretags: break
            if len(buffer) < parser.BUFFERSIZE: break
        usock.close()
        if parser.href:
            return urlparse.urljoin(url, parser.href)
        else:
            raise Exception
    except:
        return None


def _get_news_sources(artist):
    """
    Find RSS/Atom feeds avaiable for artist.

    @param artist: a CachedArtist object

    @return: a list of strings with URLs
    """
    sources = []
    future_calls = []

    if 'Myspace' in artist.urls:

        if 'myspace_id' not in artist:
            myspace_profile = artist.urls['Myspace'][0]
            myspace_id = _get_myspace_id(myspace_profile)
            artist.myspace_id = myspace_id
            artist.changes_present = True

        if 'myspace_id' in artist and artist.myspace_id:
            myspace_blog_feed = "http://blogs.myspace.com/Modules/BlogV2/Pages/RssFeed.aspx?friendID=%s" % artist.myspace_id
            sources.append(myspace_blog_feed)

    t = mmda_logger('www','request','find feeds',artist.name)

    for source_type in LOOK_FOR_FEEDS:
        if source_type in artist.urls:
            future_calls = [Future(_get_feed_link_for,url) for url in artist.urls[source_type]]

    sources.extend(list(set([url() for url in future_calls if url()])))

    mmda_logger('www','result','found feeds',len(sources),t)

    return [(src,None,None) for src in sources]

def _get_myspace_id(profile_url):
    """
    Return myspace user id.

    Be smart, and stop download if ID is found.

    @param url: a string with Myspace profile URL

    @return: a string with user id
    """
    BUFFERSIZE = 2048
    id = None
    re_myspaceid = re.compile("blogs.myspace.com/index.cfm\?fuseaction=blog.ListAll&friendId=(?P<friend_id>\d+)")

    t = mmda_logger('mspc','request','find ID',profile_url)
    try:
        usock =  HTTP_OPENER.open(profile_url, timeout=SEARCH_TIMEOUT)
        while 1:
            buffer = usock.read(BUFFERSIZE)
            r = re_myspaceid.search(buffer)
            if r and r.groups():
                id = r.groups()[0]
                break
            if len(buffer) < BUFFERSIZE: break
        usock.close()
    except Exception, e:
        mmda_logger('myspace','ERROR',e)

    mmda_logger('mspc','result','myspace ID',id,t)
    return id

