# -*- coding: utf-8
import hashlib
import musicbrainz2.webservice  as ws
import musicbrainz2.model       as m

from datetime           import datetime
from django.conf        import settings
from musicbrainz2.utils import extractUuid

from mmda.search.models import CachedSearchResult
from mmda.engine.utils  import mmda_logger

mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)
RESULTS_LIMIT = 25

def get_basic_cached_search_result(query_type, query_string):
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
    if 'mb' not in search_result.cache_state: #TODO: add 14day window check

        try:
            mmda_logger('mb','request','search for',query_string)

            if query_type == 'artist':
                filter  = ws.ArtistFilter(name=query_string,limit=RESULTS_LIMIT)
                results = q.getArtists(filter) #TODO: add try, or maybe better in 'create_search' as a global wrapper
                search_result.results = [ {'name':r.artist.name, 'mbid':extractUuid(r.artist.id), 'score':r.score, 'note':r.artist.disambiguation } for r in results ]

            elif query_type == 'release':
                filter  = ws.ReleaseFilter(title=query_string,limit=RESULTS_LIMIT)
                results = q.getReleases(filter) #TODO: add try, or maybe better in 'create_search' as a global wrapper
                search_result.results = [ {'artist':r.release.artist.name, 'title':r.release.title, 'mbid':extractUuid(r.release.id), 'artist_mbid':extractUuid(r.release.artist.id), 'score':r.score, 'tracks_count':r.release.tracksCount, 'year':r.release.getEarliestReleaseEvent().getDate() if r.release.getEarliestReleaseEvent() else None} for r in results ]

            elif query_type == 'tag':
                # TODO: refactor to other packages
                import pylast
                lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
                lastfm_similar_tags = lastfm.search_for_tag(query_string).get_next_page()
                search_result.results = [ t.name for t in lastfm_similar_tags ]

        except ws.WebServiceError, e:
            # TODO: hard error here
            mmda_logger('search','ERROR',e)
            raise Http500
        else:
            mmda_logger('mb','result','results',len(search_result.results))
            search_result.cache_state['mb'] = [1,datetime.utcnow()]
            search_result.save()
    return query_id

