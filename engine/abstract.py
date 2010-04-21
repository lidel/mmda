# -*- coding: utf-8
import surf
from datetime import datetime
from mmda.engine.utils import mmda_logger

from BeautifulSoup import BeautifulStoneSoup
from urllib2 import urlopen

ABSTRACT_TIMEOUT = 5 #seconds

def populate_abstract(artist_or_releasegroup):
    """
    Populate CachedArtist or CachedRleaseGroup with short abstract.

    High-level API aimed to replace populate_*_lastfm

    @param artist_or_releasegroup: a CachedArtist or CachedReleaseGroup object
    @return: a CachedArtist or CachedReleaseGroup object
    """
    if 'abstract' not in artist_or_releasegroup:
        abstract = get_abstract_from_bbc(artist_or_releasegroup)
        if not abstract:
            abstract = get_abstract_from_dbpedia(artist_or_releasegroup)
        # TODO: add other abstract sources here

        if abstract:
            artist_or_releasegroup.abstract = abstract

    return artist_or_releasegroup

def get_abstract_from_dbpedia(artist_or_releasegroup):
    """
    Populate CachedArtist or CachedRleaseGroup with short abstract.

    @param artist_or_releasegroup: a CachedArtist or CachedReleaseGroup object

    @return: a dictionary with an abstract structure
    """
    abstract = {}
    # if artist_or_releasegroup is ReleaseGroup, we look for release with wikipedia URL
    # TODO: check performance, and if better - replace in other parts
    # TODO: DRY: refactor
    if 'dbpedia' not in artist_or_releasegroup.cache_state:
        wiki_resource = None
        if 'releases' in artist_or_releasegroup:
            for release in artist_or_releasegroup['releases'].itervalues():
                if 'urls' in release  and 'Wikipedia' in release['urls']:
                    wiki_resource, wiki_lang, wiki_url = find_best_wikipedia_resource(release['urls']['Wikipedia'])
        elif 'urls' in artist_or_releasegroup and 'Wikipedia' in artist_or_releasegroup['urls']:
            wiki_resource, wiki_lang, wiki_url = find_best_wikipedia_resource(artist_or_releasegroup['urls']['Wikipedia'])

        if wiki_resource:
            store = surf.Store(reader = "sparql_protocol", endpoint = "http://dbpedia.org/sparql")
            session = surf.Session(store)
            sparql_query = "SELECT ?abstract WHERE {{ <http://dbpedia.org/resource/%s> <http://dbpedia.org/property/abstract> ?abstract FILTER langMatches( lang(?abstract), '%s') } }" % (wiki_resource, wiki_lang)
            try:
                t = mmda_logger('wiki','request','abstract',wiki_resource)
                # TODO: timeout?
                sparql_result = session.default_store.execute_sparql(sparql_query) # TODO: error handling
                mmda_logger('wiki','result','found',len(sparql_result['results']['bindings']),t)
                if sparql_result['results']['bindings']:
                    abstract = {'content':unicode(sparql_result['results']['bindings'][0]['abstract']), 'url':wiki_url, 'lang':wiki_lang, 'provider':'Wikipedia'}
                    # TODO: add cache_status dbpedia
            except Exception, e:
                # TODO: handle it?
                mmda_logger('surf-dbpedia','ERROR',e)
        artist_or_releasegroup.cache_state['dbpedia'] = [1,datetime.utcnow()]
        artist_or_releasegroup.changes_present = True
    return abstract

def find_best_wikipedia_resource(wikipedia_urls):
    """
    Find wikipedia resource parameters. Prefer english one, if present.

    @param wikipedia_urls: a list of URL strings

    @return: a tuple with resource name, its language and URL
    """
    for url in wikipedia_urls:
        raped_url     = url.split('/')
        wiki_resource = raped_url[-1]
        wiki_lang     = raped_url[2].split('.')[0]
        wiki_url      = url
        if wiki_lang == 'en':
            break
    return (wiki_resource, wiki_lang, wiki_url)


def get_abstract_from_bbc(artist):
    """
    Populate CachedArtist with short Wikipedia abstract from BBC API.

    BBC provide abstracts only for artists, so we skip it if argument is a release

    @param artist_or_releasegroup: a CachedArtist or CachedReleaseGroup object

    @return: a dictionary with an abstract structure
    """
    abstract = {}
    if artist._doc_type == 'CachedArtist' and 'bbc' not in artist.cache_state:
        try:
            t = mmda_logger('bbc','request','abstract',artist.get_id)
            xml = urlopen("http://www.bbc.co.uk/music/artists/%s/wikipedia.xml" % artist.get_id, timeout=ABSTRACT_TIMEOUT).read()
            xmlSoup = BeautifulStoneSoup(xml)
            abstract = {
                    'content':xmlSoup.wikipedia_article.content.text,
                    'url':xmlSoup.wikipedia_article.url.text,
                    'lang':'en',
                    'provider':'Wikipedia'
                    }
        except Exception, e:
            mmda_logger('bbc','ERROR',e)
        else:
            mmda_logger('bbc','result','found',abstract['url'],t)
        artist.cache_state['bbc'] = [1,datetime.utcnow()]
        artist.changes_present = True
    return abstract
