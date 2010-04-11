# -*- coding: utf-8
#import re
#import musicbrainz2.webservice as ws
#import musicbrainz2.model as m

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
#from couchdbkit.ext.django.loading import get_db
#from couchdbkit.resource import ResourceNotFound
#from musicbrainz2.utils import extractUuid, extractFragment
#from datetime import datetime
#from django.conf import settings

from mmda.artists.templatetags.release_helpers import slugify2
#from mmda.artists.models import CachedArtist, CachedReleaseGroup

from mmda.commons.artist import get_populated_artist, get_artist_primary_releases
from mmda.commons.release import get_populated_releasegroup_with_release

# TODO: remove/replace by a view
from mmda.commons.pictures import get_basic_artist_pictures


# TODO: check if safe as global
#db = get_db('artists')
#mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)

def index(request):
    #TODO: ee?
    return render_to_response('artists/index.html', locals())

def show_artist(request, uri_artist, mbid):
    """
    Show page of an artist specified by mbid.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered artist page or redirection to a proper URL
    """

    artist = get_populated_artist(mbid)
    primary_releases = get_artist_primary_releases(mbid)

    # TODO: make/move to  a dedicated view with required number of pics?
    artist_pictures = get_basic_artist_pictures(mbid)

    # basic SEO check
    artist_seo_name = slugify2(artist.name)
    if uri_artist == artist_seo_name:
        return render_to_response('artists/show_artist.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist', args=(artist_seo_name, mbid)))

def show_release(request, uri_artist, uri_release, mbid):
    """
    Show page of a release specified by mbid.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name
    @param uri_release: a string containing SEO-friendly release title

    @return: a rendered release page or redirection to a proper URL
    """
    release_group, release = get_populated_releasegroup_with_release(mbid)

    # basic SEO check
    artist_seo_name     = slugify2(release_group.artist_name)
    release_seo_name    = slugify2(release['title'])
    if uri_artist == artist_seo_name and uri_release == release_seo_name:
        return render_to_response('artists/show_release.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-release', args=(artist_seo_name, release_seo_name, mbid)))

