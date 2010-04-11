# -*- coding: utf-8
#from datetime import datetime
from django.shortcuts import render_to_response
from django.http import HttpResponsePermanentRedirect
#from django.conf import settings
from django.core.urlresolvers import reverse
#from django.core.cache import cache
#from couchdbkit.resource import ResourceNotFound

#from mmda.pictures.models import CachedArtistPictures
from mmda.artists.templatetags.release_helpers import slugify2
from mmda.engine.pictures import get_populated_artist_pictures

def show_artist_pictures(request, uri_artist, mbid):
    """
    Show page with photos related to specified artist.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered pictures page or a redirection to a proper URL
    """
    artist_pictures = get_populated_artist_pictures(mbid)

    # basic SEO check
    artist_seo_name = slugify2(artist_pictures.artist_name)
    if uri_artist == artist_seo_name:
        return render_to_response('pictures/show_artist_pictures.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist-pictures', args=(artist_seo_name, mbid)))

