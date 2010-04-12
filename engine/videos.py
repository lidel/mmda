# -*- coding: utf-8

from datetime import datetime
from django.conf import settings
from couchdbkit.resource import ResourceNotFound

import gdata.youtube as yt
import gdata.youtube.service as yts

from mmda.videos.models import CachedArtistVideos
from mmda.engine.artist import get_basic_artist
from mmda.engine.utils  import mmda_logger

#from django.template.defaultfilters import urlencode

YOUTUBE_MAX_RESULTS = 50

def get_populated_artist_videos(mbid):
    """
    Return populated objects required by mmda.videos.show_artist_videos

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return: a CachedArtistVideos object
    """
    artist_videos = get_basic_artist_videos(mbid)
    artist_videos = populate_artist_videos_youtube(artist_videos)
    #artist_videos = populate_artist_videos_flickr(artist_videos)

    return artist_videos

def get_basic_artist_videos(mbid):
    """
    Make sure document and its dependencies are present and contain required data.

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return:  a CachedArtistVideos object containing minimal data set
    """
    try:
        artist_videos = CachedArtistVideos.get(mbid)
        if 'artist_name' not in artist_videos:
            raise ResourceNotFound
    except ResourceNotFound:
        # overhead, but in most cases artist page
        # is a place where user will go next anyway
        artist = get_basic_artist(mbid)
        artist_videos = CachedArtistVideos.get_or_create(mbid)
        artist_videos.artist_name = artist.name
        if 'aliases' in artist:
            artist_videos.artist_aliases = list(artist.aliases)
        artist_videos.save()
    return  artist_videos

def populate_artist_videos_youtube(artist_videos):
    """
    Make sure all avaiable youtube meta-data is present in a CachedArtistVideos document.

    @param artist_videos: a CachedArtistVideos object

    @return: a validated/updated CachedArtistVideos object
    """
    # TODO : add try and except
    # TODO: expire in one week?
    if 'youtube' not in artist_videos.cache_state:
    #if True: # TODO : disable after debug

        youtube_videos = []
        yt_service = yts.YouTubeService()
        artist = get_basic_artist(artist_videos._id)

        mmda_logger('yt','request','artist-videos',artist_videos.artist_name)
        # check if artist has dedicated Youtube channel
        if 'urls' in artist and 'Youtube' in artist.urls:
            artist_videos.youtube_channel = artist.urls['Youtube'][0]
            youtube_id = _get_youtube_id(artist)

            feed = yt_service.GetYouTubeVideoFeed("http://gdata.youtube.com/feeds/api/users/%s/uploads" % youtube_id)

        # if there is no official channel, make a search query
        else:
            query = yts.YouTubeVideoQuery()

            query.orderby = 'relevance'
            query.racy = 'exclude'
            query.max_results = YOUTUBE_MAX_RESULTS
            query.categories.append('Music')

            # 'bug' workaround (http://bugs.python.org/issue1712522)
            query.vq = artist_videos.artist_name.encode('utf-8', '/')

            # TODO: aliases? atm they seems to lower the result quality
            #query.vq = u"Múm OR MÃºm OR mum OR múm".encode('utf-8', '/')

            feed = yt_service.YouTubeQuery(query)

        mmda_logger('yt','result','artist-videos',len(feed.entry))

        for entry in feed.entry:
            try:
                video = {
                        'title':    entry.media.title.text,
                        'duration': entry.media.duration.seconds,
                        'url':      entry.media.player.url,
                        'player':   entry.GetSwfUrl(),
                        'thumb':    entry.media.thumbnail[0].url
                        }
            # sometimes objects we have are wicked -- we reject them
            # eg. when official channel contains blocked in some regions videos
            # example: http://www.youtube.com/user/dreamtheater
            except (NameError, AttributeError):
                continue
            else:
                youtube_videos.append(video)

        if youtube_videos:
            artist_videos.youtube = youtube_videos
        artist_videos.cache_state['youtube'] = [1,datetime.utcnow()]
        artist_videos.save()
        mmda_logger('db','store','artist-videos',artist_videos.artist_name)
    return artist_videos

def _get_youtube_id(artist):
    """
    Return Youtube ID of an artist.

    @param artist: a CachedArtist object.

    @return: a string with Youtube ID
    """
    url = artist.urls['Youtube'][0]

    # sometimes url from MusicBrainz contains tailing slash, so..
    if url[-1:] == "/":
        url = url[0:-1]

    youtube_id = url.split('/')[-1]

    return youtube_id

# debug methods from http://code.google.com/apis/youtube/1.0/developers_guide_python.html#GettingStarted
def GetAndPrintVideoFeed(uri):
  yt_service = gdata.youtube.service.YouTubeService()
  feed = yt_service.GetYouTubeVideoFeed(uri)
  for entry in feed.entry:
    PrintEntryDetails(entry)

def PrintEntryDetails(entry):
  print 'Video title: %s' % entry.media.title.text
  #print 'Video published on: %s ' % entry.published.text
  print 'Video description: %s' % entry.media.description.text
  #print 'Video category: %s' % entry.media.category[0].text
  #print 'Video tags: %s' % entry.media.keywords.text
  print 'Video watch page: %s' % entry.media.player.url
  print 'Video flash player URL: %s' % entry.GetSwfUrl()
  print 'Video duration: %s' % entry.media.duration.seconds

  # non entry.media attributes
  #print 'Video geo location: %s' % entry.geo.location()
  #print 'Video view count: %s' % entry.statistics.view_count
  #print 'Video rating: %s' % entry.rating.average

  # show alternate formats
  #for alternate_format in entry.media.content:
  #  if 'isDefault' not in alternate_format.extension_attributes:
  #    print 'Alternate format: %s | url: %s ' % (alternate_format.type,
  #                                               alternate_format.url)

  # show thumbnails
  for thumbnail in entry.media.thumbnail:
    print 'Thumbnail url: %s' % thumbnail.url

