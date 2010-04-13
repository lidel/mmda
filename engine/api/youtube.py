# -*- coding: utf-8

from datetime import datetime
from django.conf import settings

import gdata.youtube as yt
import gdata.youtube.service as yts

from mmda.engine.artist import get_basic_artist
from mmda.engine.utils  import mmda_logger

YOUTUBE_MAX_RESULTS = 50

def populate_artist_videos_youtube(artist_videos):
    """
    Make sure all avaiable youtube meta-data is present in a CachedArtistVideos document.

    @param artist_videos: a CachedArtistVideos object

    @return: a validated/updated CachedArtistVideos object
    """
    # TODO: expire in one week?
    if 'youtube' not in artist_videos.cache_state:

        youtube_videos = []
        yt_service = yts.YouTubeService()
        artist = get_basic_artist(artist_videos._id)

        try:
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

        except Exception, e:
            mmda_logger('yt-search','ERROR',e)
            #raise Http500
        else:
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
                # TODO: what if there is no videos left?
                #       example: http://127.0.0.1:8000/artist/the-beatles/videos/b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d/
                except (NameError, AttributeError):
                    continue
                else:
                    youtube_videos.append(video)

            if youtube_videos:
                artist_videos.youtube = youtube_videos
            artist_videos.cache_state['youtube'] = [1,datetime.utcnow()]
            artist_videos.changes_present = True
            mmda_logger('db','store',artist_videos)

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


