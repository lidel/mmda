# -*- coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from mmda.search.models import CachedSearchResult
from mmda.artists.templatetags.release_helpers import slugify2
from django.core.urlresolvers import reverse
from mmda.engine.search import get_basic_cached_search_result
from couchdbkit.resource import ResourceNotFound

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
        return HttpResponseRedirect(reverse('welcome-page'))

    query_id = get_basic_cached_search_result(query_type, query_string)
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
        return HttpResponseRedirect(reverse('create-search-result', args=(query_type,query_string)))

    # SEO check
    seo_query_type   = slugify2(search_result.query_type)
    seo_query_string = slugify2(search_result.query_string)
    if query_type != seo_query_type or query_string != seo_query_string:
        return HttpResponseRedirect(reverse('show-search-result', args=(seo_query_type,seo_query_string,query_id)))

    return render_to_response("search/%s_results.html" % search_result.query_type, locals())
