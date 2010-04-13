# -*- coding: utf-8

from datetime import datetime
from django.conf import settings
from mmda.engine.utils import mmda_logger, save_any_document_changes
from mmda.pictures.models import CachedArtistPictures
from couchdbkit.resource import ResourceNotFound

from mmda.engine.artist import get_basic_artist

from mmda.engine.api.lastfm import populate_artist_pictures_lastfm
from mmda.engine.api.flickr import populate_artist_pictures_flickr


def get_populated_artist_pictures(mbid):
    """
    Return populated objects required by mmda.pictures.show_artist_pictures

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return: a CachedArtistPictures object
    """
    artist_pictures = get_basic_artist_pictures(mbid)

    artist_pictures = populate_artist_pictures_lastfm(artist_pictures)
    artist_pictures = populate_artist_pictures_flickr(artist_pictures)

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

