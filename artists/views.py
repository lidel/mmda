# -*- coding: utf-8
from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from mmda.artists.templatetags.release_helpers import slugify2

from mmda.engine.artist import get_recent_artists, get_basic_artist, get_artist_cache_state, get_populated_artist, get_artist_primary_releases, get_artist_best_pictures
from mmda.engine.release import get_populated_releasegroup_with_release
from mmda.engine.cache import delete_memcached_keys

import recaptcha.client.captcha as rc
from mmda.engine.api.recaptcha import get_captcha_html

from couchdbkit.resource import ResourceNotFound
from couchdbkit.ext.django.loading import get_db

def index(request):
    #TODO: ee?
    recent_artists = get_recent_artists()
    return render_to_response('index.html', locals())

def show_artist(request, uri_artist, mbid):
    """
    Show page of an artist specified by mbid.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered artist page or redirection to a proper URL
    """
    artist              = get_populated_artist(mbid)
    primary_releases    = get_artist_primary_releases(mbid)
    artist_pictures     = get_artist_best_pictures(mbid)

    # basic SEO check
    artist_seo_name = slugify2(artist.name)
    if uri_artist == artist_seo_name:
        return render_to_response('artists/show_artist.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist', args=(artist_seo_name, mbid)))

def show_artist_refresh(request, uri_artist, mbid):
    """
    Show reset page of an artist specified by mbid.

    If request contains POST data, perform reset.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered artist page
    """
    if request.POST:
        mbid            = request.POST['mbid']
        reset           = request.POST.getlist('reset')

        rc_ip           = request.META['REMOTE_ADDR']
        rc_token        = request.POST['recaptcha_challenge_field']
        rc_input        = request.POST['recaptcha_response_field']
        captcha = rc.submit(rc_token, rc_input, settings.RECAPTCHA_PRIV_KEY, rc_ip)

        if captcha.is_valid:
            delete_memcached_keys(get_basic_artist(mbid))
            for db in reset:
                try:
                    del get_db(db)[mbid]
                except:
                    continue
            if 'artists' in reset:
                release_groups = get_db('artists').view('artists/release_groups', key=mbid)
                for group in release_groups:
                    del get_db('artists')[group['id']]
            # TODO: remove 'lastfm' from artist cache_state if pictures were removed.

    artist              = get_basic_artist(mbid)
    artist_cache_state  = get_artist_cache_state(mbid)
    html_for_captcha    = get_captcha_html(rc.API_SERVER)
    return render_to_response('artists/show_artist_refresh.html', locals())


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

