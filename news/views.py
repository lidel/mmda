# -*- coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse

from mmda.artists.templatetags.release_helpers import slugify2
from mmda.engine.news import get_populated_artist_news
from mmda.engine.artist import get_basic_artist

def show_artist_news(request, uri_artist, mbid):
    """
    Show page with news related to a specified artist.

    @param mbid:        a string containing a MusicBrainz ID of an artist
    @param uri_artist:  a string containing SEO-friendly artist name

    @return: a rendered news page or a redirection to a proper URL
    """
    artist = get_basic_artist(mbid)
    recent_news = get_populated_artist_news(artist)

    #artist.save_any_changes()

    # basic SEO check
    artist_seo_name = slugify2(artist.name)
    if uri_artist == artist_seo_name:
        return render_to_response('news/show_artist_news.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist-news', args=(artist_seo_name, mbid)))

