# -*- coding: utf-8
import flickrapi

from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from mmda.commons.utils import mmda_logger

FLICKR_LIMIT=50

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

