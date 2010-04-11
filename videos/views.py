# -*- coding: utf-8

from datetime import datetime
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from couchdbkit.resource import ResourceNotFound

from mmda.videos.models import CachedArtistVideos
from mmda.artists.templatetags.release_helpers import slugify2

def show_artist_videos(request, uri_artist, mbid):
    """
    Show page with videos related to specified artist.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered videos page or a redirection to a proper URL
    """
    artist_videos = get_basic_artist_videos(mbid)
    #artist_videos = populate_artist_videos_flickr(artist_videos)

    # basic SEO check
    artist_seo_name = slugify2(artist_videos.artist_name)
    if uri_artist == artist_seo_name:
        return render_to_response('pictures/show_artist_videos.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist-videos', args=(artist_seo_name, mbid)))

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
        from mmda.artists.views import get_basic_artist
        artist = get_basic_artist(mbid)
        artist_videos = CachedArtistVideos.get_or_create(mbid)
        artist_videos.artist_name = artist.name
        if 'aliases' in artist:
            artist_videos.artist_aliases = list(artist.aliases)
        artist_videos.save()
    return  artist_videos

def populate_artist_videos_youtube(artist_videos):
    """
    Make sure all avaiable youtube meta-data is present in a CachedArtistVideos document.

    @param artist_videos: a CachedArtistVideos object

    @return: a validated/updated CachedArtistVideos object
    """
    from mmda.artists.views import mmda_logger # TODO: cleanup
    if 'youtube' not in artist_videos.cache_state or artist_videos.cache_state['youtube'][0] == 1:
        pass
    return artist_videos

