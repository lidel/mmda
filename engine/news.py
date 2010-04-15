# -*- coding: utf-8
from datetime import datetime
from mmda.engine.utils  import mmda_logger
from mmda.engine.future import Future


def get_recent_artist_news(mbid):
    recent_news = []

    news_sources = [ "http://...", "...", "..." ]
    # pull down all feeds
    future_calls = [Future(feedparser.parse,rss_url) for rss_url in news_sources]
    # block until they are all in
    feeds = [future_obj() for future_obj in future_calls]

    entries = []
    for feed in feeds:
        entries.extend( feed[ "items" ] )

    decorated = [(entry["date_parsed"], entry) for entry in entries]
    decorated.sort()
    decorated.reverse() # for most recent entries first
    sorted = [entry for (date,entry) in decorated]


    return recent_news
