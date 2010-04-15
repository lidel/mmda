# -*- coding: utf-8

from couchdbkit.resource import ResourceNotFound

from mmda.videos.models import CachedArtistVideos
from mmda.engine.artist import get_basic_artist
from mmda.engine.api.youtube import populate_artist_videos_youtube
from mmda.engine.utils  import mmda_logger

from mmda.engine.future import Future

def get_populated_artist_videos(mbid):
    """
    Return populated objects required by mmda.videos.show_artist_videos

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return: a CachedArtistVideos object
    """
    artist_videos = get_basic_artist_videos(mbid)

    futured_youtube = Future(populate_artist_videos_youtube,artist_videos)
    artist_videos = futured_youtube()

    artist_videos.save_any_changes()

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
        # TODO: just an idea: create a view that store only names and aliases?
        artist_videos = CachedArtistVideos.get_or_create(mbid)
        artist_videos.artist_name = artist.name
        if 'aliases' in artist:
            artist_videos.artist_aliases = list(artist.aliases)
        artist_videos.save()
        mmda_logger('db','store', artist_videos)
    return  artist_videos

