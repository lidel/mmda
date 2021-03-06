# -*- coding: utf-8

from datetime import datetime
from django.conf import settings
from mmda.engine.utils import mmda_logger
from mmda.pictures.models import CachedArtistPictures
from couchdbkit.resource import ResourceNotFound

from mmda.engine.artist import get_basic_artist

from mmda.engine.api.lastfm import populate_artist_pictures_lastfm
from mmda.engine.api.flickr import populate_artist_pictures_flickr

from mmda.engine.future import Future

def get_populated_artist_pictures(mbid):
    """
    Return populated objects required by mmda.pictures.show_artist_pictures

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return: a CachedArtistPictures object
    """
    artist_pictures = get_basic_artist_pictures(mbid)

    futured_lastfm = Future(populate_artist_pictures_lastfm, artist_pictures)
    futured_flickr = Future(populate_artist_pictures_flickr, artist_pictures)

    artist_pictures = futured_lastfm()
    artist_pictures = futured_flickr()

    artist_pictures.save_any_changes()

    return artist_pictures

def get_basic_artist_pictures(mbid):
    """
    Make sure document and its dependencies are present and contain required data.

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return:  a CachedArtistPictures object containing minimal data set
    """
    try:
        artist_pictures = CachedArtistPictures.get(mbid)
        if 'artist_name' not in artist_pictures:
            raise ResourceNotFound
        mmda_logger('db','present',artist_pictures._doc_type, artist_pictures.get_id)
    except ResourceNotFound:
        # overhead, but in most cases artist page
        # is a place where user will go next anyway
        artist_pictures = CachedArtistPictures.get_or_create(mbid)
        artist = get_basic_artist(mbid)
        artist_pictures.artist_name = artist.name
        if 'aliases' in artist:
            artist_pictures.artist_aliases = list(artist.aliases)
        artist_pictures.save()
        mmda_logger('db','store', artist_pictures)
    return  artist_pictures

