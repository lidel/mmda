# -*- coding: utf-8
import pylast
import flickrapi

from datetime import datetime
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.cache import cache
from couchdbkit.resource import ResourceNotFound

from mmda.pictures.models import CachedArtistPictures
from mmda.artists.templatetags.release_helpers import slugify2
from mmda.commons.utils import mmda_logger

LASTFM_LIMIT=20
FLICKR_LIMIT=50

def show_artist_pictures(request, uri_artist, mbid):
    """
    Show page with photos related to specified artist.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered pictures page or a redirection to a proper URL
    """
    artist_pictures = initiate_artist_pictures(mbid)
    artist_pictures = populate_artist_pictures_lastfm(artist_pictures)
    artist_pictures = populate_artist_pictures_flickr(artist_pictures)

    # basic SEO check
    artist_seo_name = slugify2(artist_pictures.artist_name)
    if uri_artist == artist_seo_name:
        return render_to_response('pictures/show_artist_pictures.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist-pictures', args=(artist_seo_name, mbid)))

def initiate_artist_pictures(mbid):
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
        from mmda.artists.views import initiate_artist
        artist = initiate_artist(mbid)
        artist_pictures = CachedArtistPictures.get_or_create(mbid)
        artist_pictures.artist_name = artist.name
        if 'aliases' in artist:
            artist_pictures.artist_aliases = list(artist.aliases)
        artist_pictures.save()
    return  artist_pictures

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
            mmda_logger('last','request','artist-pictures',artist_pictures._id)
            lastfm_artist = lastfm.get_artist_by_mbid(artist_pictures._id)
            lastfm_images = lastfm_artist.get_images(limit=LASTFM_LIMIT) #TODO: make 50?
            # TODO: add lastfm event info, that can be used as a tag in flickr search
            mmda_logger('last','result','artist-pictures',artist_pictures._id)
        except Exception, e:
            print 'Error pylast:', e
        else:
            if lastfm_images:
                artist_pictures.lastfm = [ {'sq':i.sizes.largesquare, 'big':i.sizes.extralarge, 'url':i.url,'title':i.title} for i in lastfm_images]
            artist_pictures.cache_state['lastfm'] = [2,datetime.utcnow()]
            artist_pictures.save()
            mmda_logger('db','store','[last.fm] artist pictures',artist_pictures._id)


    return artist_pictures

def populate_artist_pictures_flickr(artist_pictures):
    """
    Make sure desired flickr pictures are present in a CachedArtistPictures document.

    @param artist_pictures: a CachedArtistPictures object

    @return: a validated/updated CachedArtistPictures object
    """
    # TODO: cache flickr only for a day?
    if 'flickr' not in artist_pictures.cache_state:
        flickr = flickrapi.FlickrAPI(settings.FLICKR_API_KEY, cache=True)
        flickr.cache = cache

        # TODO: use artist aliases  as alternative tags? (what about tag_mode?)
        artist_tags = artist_pictures.artist_name
        if 'artist_aliases' in artist_pictures:
            artist_tags += ',' + ','.join(artist_pictures.artist_aliases)

        includes = 'owner_name, url_sq, url_m'
        licenses = '1,2,3,4,5,6,7' # http://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html

        data_walker = flickr.walk(tag_mode='any',tags=artist_tags.lower(),media='photos',license=licenses,extras=includes,per_page=FLICKR_LIMIT)
        # TODO: make two walks. first one with events from lastfm, second if result list is less than FLICKR_LIMIT

        flickr_photos = []
        try:
            for i in xrange(FLICKR_LIMIT):
                f_photo = data_walker.next()
                f_photo_url = "http://www.flickr.com/photos/%s/%s" % (f_photo.get('owner'), f_photo.get('id'))
                photo = {'title':f_photo.get('title'), 'sq':f_photo.get('url_sq'), 'big':f_photo.get('big'), 'url':f_photo_url, 'owner':f_photo.get('ownername')}
                flickr_photos.append(photo)
        except Exception, e:
            print 'Error flickrapi:', e
        if flickr_photos:
            artist_pictures.flickr = flickr_photos
            artist_pictures.cache_state['flickr'] = [2,datetime.utcnow()]
            artist_pictures.save()
            mmda_logger('db','store','[flickr] artist pictures',artist_pictures._id)

    return artist_pictures

