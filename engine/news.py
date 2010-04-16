# -*- coding: utf-8
from datetime import datetime
from mmda.engine.utils  import mmda_logger
from mmda.engine.future import Future

import feedparser
import re


def get_recent_artist_news(artist):
    recent_news = []

    news_sources = _get_news_sources(artist)
    # pull down all feeds
    t = mmda_logger('news','request','feeds',len(news_sources))
    future_calls = [Future(feedparser.parse,rss_url) for rss_url in news_sources]
    # block until they are all in
    feeds = [future_obj() for future_obj in future_calls]

    entries = []
    for feed in feeds:
        #items = [{'content':i['content'],'date_parsed':i['date_parsed']} for i in feed['items']]
        print 'no'
        if feed.feed.link.startswith('http://blog.myspace'):
            myspace_entries = [ {'title':e.title, 'summary':e.summary, 'date':e.updated, 'url':e.link, 'src':'Myspace'} for e in feed['items']]

            entries.extend(myspace_entries)

    decorated = [(entry["date"], entry) for entry in entries]
    decorated.sort()
    decorated.reverse() # for most recent entries first
    sorted = [entry for (date,entry) in decorated]
    return sorted

def _get_news_sources(artist):
    """
    Find RSS/Atom feeds avaiable for artist.

    @param artist: a CachedArtist object

    @return: a list of strings with URLs
    """
    sources = []
    if 'Myspace' in artist.urls:
        #if 'myspace_id' not in artist:
        if True: # TODO: remove
            print 'lol'
            # TODO: add try
            myspace_name = _get_myspace_username(artist)
            t = mmda_logger('myspace','request','activity stream',myspace_name)
            activity_feed = "http://www.myspace.com/%s/stream/atom.xml" % myspace_name
            myspace_id = _get_myspace_id( feedparser.parse(activity_feed) )
            artist.myspace_id = myspace_id
            artist.changes_present = True
            myspace_blog_feed = "http://blogs.myspace.com/Modules/BlogV2/Pages/RssFeed.aspx?friendID=%s" % myspace_id
            sources.append(myspace_blog_feed)
            mmda_logger('myspace','result','found ID and blog',myspace_id,t)

    return sources

def _get_myspace_username(artist):
    """
    Return myspace user name.

    @param url: a string with URL

    @return: a string with user name
    """
    url = artist.urls['Myspace'][0]

    # sometimes url from MusicBrainz contains tailing slash, so..
    if url[-1:] == "/":
        url = url[0:-1]

    myspace_name = url.split('/')[-1]

    return myspace_name

def _get_myspace_id(activity_feed):
    myspaceid_regex = re.compile("friendId=(?P<friend_id>\d+)")
    # TODO: add try:, return None if fail
    html = activity_feed['items'][0]['content'][0]['value']
    r = myspaceid_regex.search(html)
    # r.match(html)
    return r.groups()[0]
