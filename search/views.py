# -*- coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from mmda.search.models import CachedSearchResult
import musicbrainz2.webservice as ws
import musicbrainz2.model as m
from mmda.artists.templatetags.release_helpers import slugify2
from django.core.urlresolvers import reverse
from musicbrainz2.utils import extractUuid
import hashlib
from datetime import datetime
from django.conf import settings
from mmda.artists.views import mmda_logger

RESULTS_LIMIT = 25

mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)

def create_search_result(request, query_type=None, query_string=None):
    """
    Process POST and RESTful search query and redirect to result page.

    Each query has its own ID and results page has permanent URL.
    (eg. one can copy URL it and show to someone else)

    @param query_type: an optional string containing query type
    @param query_string: an optional string containing query

    @return: a HttpResponseRedirect object
    """
    if request.POST:
        query_string    = request.POST.get('query', '').strip().lower()
        query_type      = request.POST.get('type', '')
    # TODO: not sure why, but this code makes me feel ugly
    elif not query_string or not query_type:
        return HttpResponseRedirect(reverse('welcome-page')) #TODO: HttpResponsePermanentRedirect when url-schema is mature

    # TODO: escape fix all possible problems?
    query_id = initialize_cached_search_result(query_type, query_string)
    return HttpResponseRedirect(reverse('show-search-result', args=(slugify2(query_type),slugify2(query_string),query_id)))

def show_search_result(request, query_type, query_string, query_id):
    """
    Display CachedSearchResult.

    If document is missing create new one using RESTful query redirect.

    @param query_type: a string containing query type
    @param query_string: a string containing query
    @param query_id: a string containing an ID of a CachedSearchResult document

    @return: a HttpResponseRedirect object or rendered search result page
    """
    # TODO: add meta-header for robots: nocahe, norobots etc
    try:
        search_result = CachedSearchResult.get(query_id)
    except ResourceNotFound:
        return HttpResponseRedirect(reverse('redirect-to-search-result', args=(query_type,query_string))) #TODO: HttpResponsePermanentRedirect when url-schema is mature


    # SEO check
    # TODO: refactor globally?
    seo_query_type   = slugify2(search_result.query_type)
    seo_query_string = slugify2(search_result.query_string)
    if query_type != seo_query_type or query_string != seo_query_string:
        return HttpResponseRedirect(reverse('show-search-result', args=(seo_query_type,seo_query_string,query_id))) #TODO: HttpResponsePermanentRedirect when url-schema is mature


    if search_result.query_type == 'artist':
        return render_to_response('search/artist_results.html', locals())
    elif search_result.query_type == 'release':
        return render_to_response('search/release_results.html', locals())

def initialize_cached_search_result(query_type, query_string):
    """
    Make sure proper CachedSearchResult is present and return its id.

    Method performs local, then optional remote (MusicBrainz) lookup of query result

    @param query_type: a string containing query type
    @param query_string: a string containing query

    @return: a string containing SHA1 hash of a query string (the ID of a CachedSearchResult document)
    """
    query_id        = hashlib.sha1((query_type+query_string).encode('utf-8')).hexdigest()
    search_result   = CachedSearchResult.get_or_create(query_id)
    search_result.query_string  = query_string
    search_result.query_type    = query_type
    q = ws.Query(mb_webservice)
    if search_result.cache_state['mb'][0] == 0: #TODO: add 14day window check
        if query_type == 'artist':
            filter  = ws.ArtistFilter(name=query_string,limit=RESULTS_LIMIT)
            results = q.getArtists(filter) #TODO: add try, or maybe better in 'create_search' as a global wrapper
            search_result.results = [ {'name':r.artist.name, 'mbid':extractUuid(r.artist.id), 'score':r.score, 'note':r.artist.disambiguation } for r in results ]
        elif query_type == 'release':
            filter  = ws.ReleaseFilter(title=query_string,limit=RESULTS_LIMIT)
            results = q.getReleases(filter) #TODO: add try, or maybe better in 'create_search' as a global wrapper
            search_result.results = [ {'artist':r.release.artist.name, 'title':r.release.title, 'mbid':extractUuid(r.release.id), 'artist_mbid':extractUuid(r.release.artist.id), 'score':r.score, 'tracks_count':r.release.tracksCount, 'year':r.release.getEarliestReleaseEvent().getDate() if r.release.getEarliestReleaseEvent() else None} for r in results ]
        search_result.cache_state['mb'] = [1,datetime.utcnow()]
        search_result.save()
    return query_id

