# -*- coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse

from mmda.artists.templatetags.release_helpers import slugify2
from mmda.engine.videos import get_populated_artist_videos

def show_artist_videos(request, uri_artist, mbid):
    """
    Show page with videos related to a specified artist.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered videos page or a redirection to a proper URL
    """
    artist_videos = get_populated_artist_videos(mbid)

    # basic SEO check
    artist_seo_name = slugify2(artist_videos.artist_name)
    if uri_artist == artist_seo_name:
        return render_to_response('videos/show_artist_videos.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist-videos', args=(artist_seo_name, mbid)))

