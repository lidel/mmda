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

mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)

def create_search(request):
    """
    Process search query and redirect to result page.
    """
    query           = request.POST.get('query', '').strip().lower()
    query_type      = request.POST.get('type', '')
    query_id        = initialize_cached_search_result(query,query_type)
    # TODO zrobic ladny url? /search/artist/string/hash
    return HttpResponseRedirect(reverse('show-search-result', args=(query_id,))) #TODO: HttpResponsePermanentRedirect when url-schema is mature

def show_search_result(request, query_id):
    """
    Display CachedSearchResult.
    """
    # TODO: handle 404/no result scenario better
    # TODO: add meta-header for robots: nocahe, norobots etc
    search_result = CachedSearchResult.get(query_id)
    if search_result.query_type == 'artist':
        return render_to_response('search/artist_results.html', locals())
    elif search_result.query_type == 'release':
        return render_to_response('search/release_results.html', locals())

def initialize_cached_search_result(query, query_type):
    """
    Make sure proper CachedSearchResult is present and return its id.

    Method performs local, then optional remote (MusicBrainz) lookup of query result
    """
    query_id        = hashlib.sha1((query+query_type).encode('utf-8')).hexdigest()
    search_result   = CachedSearchResult.get_or_create(query_id)
    q               = ws.Query(mb_webservice)
    search_result.query         = query
    search_result.query_type    = query_type
    if search_result.cache_state['mb'][0] == 0: #TODO: add 14day window check
        if query_type == 'artist':
            filter  = ws.ArtistFilter(name=query,limit=25)
            results = q.getArtists(filter) #TODO: add try, or maybe better in 'create_search' as a global wrapper
            search_result.results = [ {'name':r.artist.name, 'mbid':extractUuid(r.artist.id), 'score':r.score, 'disambiguation':r.artist.disambiguation } for r in results ]
        elif query_type == 'release':
            filter  = ws.ReleaseFilter(title=query,limit=25)
            results = q.getReleases(filter) #TODO: add try, or maybe better in 'create_search' as a global wrapper
            search_result.results = [ {'artist':r.release.artist.name, 'title':r.release.title, 'mbid':extractUuid(r.release.id), 'artist_mbid':extractUuid(r.release.artist.id), 'score':r.score, 'tracks_count':r.release.tracksCount, 'year':r.release.getEarliestReleaseEvent().getDate() if r.release.getEarliestReleaseEvent() else None} for r in results ]
    search_result.cache_state['mb'] = [1,datetime.utcnow()]
    search_result.save()
    return query_id

