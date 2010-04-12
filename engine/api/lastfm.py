# -*- coding: utf-8
import pylast

from datetime import datetime
from django.conf import settings
from mmda.engine.utils import mmda_logger
from django.utils.html import strip_tags
from mmda.pictures.models import CachedArtistPictures

LASTFM_LIMIT=20

def populate_artist_lastfm(artist):
    """
    Make sure all required and avaiable last.fm data is present in a CachedArtist document.

    @param artist: a CachedArtist object

    @return: a validated/updated CachedArtist object
    """
    if 'lastfm' not in artist.cache_state:
        lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
        lastfm.enable_caching()
        try:
            mmda_logger('last','request','artist-data',artist._id)
            lastfm_artist = lastfm.get_artist_by_mbid(artist._id)
            # TODO: run there in parallel (?)
            lastfm_images = lastfm_artist.get_images(limit=5)
            lastfm_url    = lastfm_artist.get_url()
            # we get similar artists from lastfm database, but only those with mbid (omg, omg)
            # TODO: think about numbers of fetched things
            lastfm_similar  = lastfm_get_similar_optimized(lastfm_artist,limit=10)
            lastfm_tags     = lastfm_artist.get_top_tags(limit=10)
            lastfm_abstract = None
            if 'abstract' not in artist:
                lastfm_abstract = lastfm_artist.get_bio_summary()
            mmda_logger('last','result','artist-data',artist._id)
        except Exception, e:
            mmda_logger('pylast','ERROR',e)
        else:
            # TODO: make it compatible with tags imported from mb (TODO2: add tags from MusicBrainz)

            # TODO: remove random?
            import random
            random.shuffle(lastfm_tags)

            if lastfm_abstract:
                artist.abstract = {'content':strip_tags(lastfm_abstract), 'lang':'en', 'provider':'Last.fm', 'url':lastfm_url}

            artist.tags                     = [(t.item.name.lower(), int( float(t.weight)/(float(100)/float(4)) ) ) for t in lastfm_tags]
            artist.similar                  = lastfm_similar
            artist.urls['Last.fm']          = [lastfm_url]

            # TODO: optimize
            if lastfm_images:
                artist_pictures = CachedArtistPictures.get_or_create(artist._id)
                if 'lastfm' not in artist_pictures:
                    artist_pictures.artist_name = artist.name
                    artist_pictures.lastfm = [ {'sq':i.sizes.largesquare, 'big':i.sizes.extralarge, 'url':i.url,'title':i.title} for i in lastfm_images]
                    artist_pictures.cache_state['lastfm'] = [1,datetime.utcnow()]
                    artist_pictures.save()
                    mmda_logger('db','store','[last.fm] artist pictures',artist._id)

            mmda_logger('db','store','[last.fm data] artist',artist._id)
        # if fail, store state too -- to avoid future attempts
        artist.cache_state['lastfm']    = [1,datetime.utcnow()]
        artist.save()
    return artist

def populate_release_lastfm(release_group, release_mbid):
    """
    Make sure all required and avaiable last.fm data is present in a CachedReleaseGroup document.

    @param release_group: a CachedReleaseGroup object
    @param release_mbid:  a string containing a MusicBrainz ID of a release

    @return: a validated/updated CachedReleaseGroup object
    """
    #if release_group.cache_state['lastfm'][0] == 0:
    release = release_group.releases[release_mbid]
    if 'lastfm' not in release_group.cache_state:
        lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
        lastfm.enable_caching()
        try:
            mmda_logger('last','request','release-data',release_mbid)

            lastfm_album = lastfm.get_album_by_mbid(release_mbid)

            lastfm_abstract = None
            lastfm_cover    = None
            lastfm_url      = lastfm_album.get_url()

            if 'abstract' not in release_group:
                lastfm_abstract = lastfm_album.get_wiki_summary()
            if 'cover' not in release:
                lastfm_cover = lastfm_album.get_cover_image()

            mmda_logger('last','result','release-data',release_mbid)
        except Exception, e:
            mmda_logger('pylast','ERROR',e)
        else:
                if 'urls' not in release:
                    release['urls'] = {}
                release['urls']['Last.fm'] = [lastfm_url]

                if lastfm_abstract:
                    release_group.abstract = {'content':strip_tags(lastfm_abstract), 'lang':'en', 'provider':'Last.fm', 'url':lastfm_url}

                if lastfm_cover:
                    release['cover'] = lastfm_cover

        # TODO: when to save? when failed do we retry?
        release_group.cache_state['lastfm']    = [1,datetime.utcnow()]
        release_group.save()
    return release_group

def lastfm_get_similar_optimized(lastfm_artist,limit=10):
    """
    Get similar artists from last.fm API in optimized way.

    Currently the only way to get mbids of such artists in pylast is item.get_mbid() method,
    which invokes 'artist.getInfo()' API method -- this is an overhead of one additional http request for each similar artist.
    It is redundant, since mbids are already in obtained XML, but pylast architecture ignores it atm.
    This method is a necessary workaround.

    @param lastfm_artist: a pylast.Artist object
    @param limit: number of similar artist to get

    @return:  a dictionary with artist name, score and mbid
    """
    params = lastfm_artist._get_params()
    params['limit'] = pylast._unicode(limit)
    doc = lastfm_artist._request('artist.getSimilar', True, params)
    names = pylast._extract_all(doc, "name")
    mbids = pylast._extract_all(doc, "mbid")
    matches = pylast._extract_all(doc, "match")
    similar_artists = []
    for i in range(0, len(names)):
        if mbids[i]:
            similar_artists.append({'name':names[i], 'score':int(float(matches[i])*100), 'mbid':mbids[i]})
    # TODO: catch and store images?
    return similar_artists

def populate_artist_pictures_lastfm(artist_pictures):
    """
    Make sure all avaiable last.fm data is present in a CachedArtistPictures document.

    @param artist_pictures: a CachedArtistPictures object

    @return: a validated/updated CachedArtistPictures object
    """
    if 'lastfm' not in artist_pictures.cache_state or artist_pictures.cache_state['lastfm'][0] == 1:
        lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
        lastfm.enable_caching()
        try:
            mmda_logger('last','request','artist pictures',artist_pictures._id)
            lastfm_artist = lastfm.get_artist_by_mbid(artist_pictures._id)
            lastfm_images = lastfm_artist.get_images(limit=LASTFM_LIMIT) #TODO: make 50?
            # TODO: add lastfm event info, that can be used as a tag in flickr search
            mmda_logger('last','result','found pictures',len(lastfm_images))
        except Exception, e:
            mmda_logger('pylast','ERROR',e)
        else:
            if lastfm_images:
                artist_pictures.lastfm = [ {'sq':i.sizes.largesquare, 'big':i.sizes.extralarge, 'url':i.url,'title':i.title} for i in lastfm_images]
            artist_pictures.cache_state['lastfm'] = [2,datetime.utcnow()]
            artist_pictures.save()
            mmda_logger('db','store','[last.fm] artist pictures',artist_pictures._id)

    return artist_pictures


