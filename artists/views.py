# -*- coding: utf-8
import re
import pylast
import surf
import musicbrainz2.webservice as ws
import musicbrainz2.model as m

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from couchdbkit.ext.django.loading import get_db
from couchdbkit.resource import ResourceNotFound
from musicbrainz2.utils import extractUuid, extractFragment
from datetime import datetime
from django.conf import settings

from mmda.artists.templatetags.release_helpers import slugify2
from mmda.artists.models import CachedArtist, CachedReleaseGroup
from mmda.pictures.models import CachedArtistPictures

from mmda.commons.utils import mmda_logger

# TODO: remove/replace by a view
from mmda.pictures.views import initiate_artist_pictures


# TODO: check if safe as global
db = get_db('artists')
mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)

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

    artist = initiate_artist(mbid)

    # used only by show_artist.html
    artist = populate_abstract(artist)
    artist = populate_artist_lastfm(artist)

    release_groups_view = db.view('artists/release_groups', key=mbid)
    release_groups = [group['value'] for group in release_groups_view.all()]

    # TODO: make/move to  a dedicated view with required number of pics?
    artist_pictures = initiate_artist_pictures(mbid)

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
    release_group   = initiate_release(mbid)
    artist          = initiate_artist(release_group.artist_mbid)
    release_group   = populate_deep_release_mb(release_group, mbid)
    release         = release_group.releases[mbid]

    # used only by show_release.html
    release_group   = populate_abstract(release_group)
    release_group   = populate_release_lastfm(release_group, mbid)
    #

    release         = release_group.releases[mbid]

    # basic SEO check
    artist_seo_name     = slugify2(artist.name)
    release_seo_name    = slugify2(release['title'])
    if uri_artist == artist_seo_name and uri_release == release_seo_name:
        return render_to_response('artists/show_release.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-release', args=(artist_seo_name, release_seo_name, mbid)))

def initiate_artist(mbid):
    """
    Make sure artist document is present and contains required data.

    @param mbid:    a string containing a MusicBrainz ID of an artist

    @return: a CachedArtist object containing required minimal data set
    """
    #TODO: handle Various Artists' artist (m.VARIOUS_ARTISTS_ID)
    try:
        artist = CachedArtist.get(mbid)
    except ResourceNotFound:
        artist = create_mb_artist(mbid)
    return  artist

def initiate_release(mbid):
    """
    Make sure release and its dependencies are present and contain required data.

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return:  a CachedReleaseGroup object containing required minimal data set
    """
    release_group   = CachedReleaseGroup.view('artists/releases',include_docs=True, key=mbid).one()
    if not release_group:
        # TODO: optimize? its just one additional request on rare ocassions tho..
        q = ws.Query(mb_webservice)
        try:
            mmda_logger('mb','request','artist mbid of release',mbid)
            mb_release  = q.getReleaseById(mbid, ws.ReleaseIncludes(artist=True))
            artist_mbid = extractUuid(mb_release.artist.id)
            mmda_logger('mb','result','artist mbid',artist_mbid)
        except ws.WebServiceError, e:
            # TODO: add error handling here
            print '[!] ->\tMusicBrainz release (special) ERROR:', e
        else:
            initiate_artist(artist_mbid)
            release_group = CachedReleaseGroup.view('artists/releases',include_docs=True, key=mbid).one()
    return release_group

def populate_artist_lastfm(artist):
    """
    Make sure all required and avaiable last.fm data is present in a CachedArtist document.

    @param artist: a CachedArtist object

    @return: a validated/updated CachedArtist object
    """
    if 'lastfm' not in artist.cache_state:
        lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
        lastfm.enable_caching()
        try:
            mmda_logger('last','request','artist-data',artist._id)
            lastfm_artist = lastfm.get_artist_by_mbid(artist._id)
            # TODO: run there in parallel (?)
            lastfm_images = lastfm_artist.get_images(limit=5)
            lastfm_url    = lastfm_artist.get_url()
            # we get similar artists from lastfm database, but only those with mbid (omg, omg)
            # TODO: think about numbers of fetched things
            lastfm_similar  = lastfm_get_similar_optimized(lastfm_artist,limit=10)
            lastfm_tags     = lastfm_artist.get_top_tags(limit=10)
            lastfm_abstract = None
            if 'abstract' not in artist:
                lastfm_abstract = lastfm_artist.get_bio_summary()
            mmda_logger('last','result','artist-data',artist._id)
        except Exception, e:
            print 'Error pylast:', e
        else:
            # TODO: make it compatible with tags imported from mb (TODO2: add tags from MusicBrainz)

            # TODO: remove random?
            import random
            random.shuffle(lastfm_tags)

            if lastfm_abstract:
                artist.abstract = {'content':strip_tags(lastfm_abstract), 'lang':'en', 'provider':'Last.fm', 'url':lastfm_url}

            artist.tags                     = [(t.item.name.lower(), int( float(t.weight)/(float(100)/float(4)) ) ) for t in lastfm_tags]
            artist.similar                  = lastfm_similar
            artist.urls['Last.fm']          = [lastfm_url]

            # TODO: optimize
            if lastfm_images:
                artist_pictures = CachedArtistPictures.get_or_create(artist._id)
                if 'lastfm' not in artist_pictures:
                    artist_pictures.artist_name = artist.name
                    artist_pictures.lastfm = [ {'sq':i.sizes.largesquare, 'big':i.sizes.extralarge, 'url':i.url,'title':i.title} for i in lastfm_images]
                    artist_pictures.cache_state['lastfm'] = [1,datetime.utcnow()]
                    artist_pictures.save()
                    mmda_logger('db','store','[last.fm] artist pictures',artist._id)

            mmda_logger('db','store','[last.fm data] artist',artist._id)
        # if fail, store state too -- to avoid future attempts
        artist.cache_state['lastfm']    = [1,datetime.utcnow()]
        artist.save()
    return artist

def populate_release_lastfm(release_group, release_mbid):
    """
    Make sure all required and avaiable last.fm data is present in a CachedReleaseGroup document.

    @param release_group: a CachedReleaseGroup object
    @param release_mbid:  a string containing a MusicBrainz ID of a release

    @return: a validated/updated CachedReleaseGroup object
    """
    #if release_group.cache_state['lastfm'][0] == 0:
    release = release_group.releases[release_mbid]
    if 'lastfm' not in release_group.cache_state:
        lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
        lastfm.enable_caching()
        try:
            mmda_logger('last','request','release-data',release_mbid)

            lastfm_album = lastfm.get_album_by_mbid(release_mbid)

            lastfm_abstract = None
            lastfm_cover    = None
            lastfm_url      = lastfm_album.get_url()

            if 'abstract' not in release_group:
                lastfm_abstract = lastfm_album.get_wiki_summary()
            if 'cover' not in release:
                lastfm_cover = lastfm_album.get_cover_image()

            mmda_logger('last','result','release-data',release_mbid)
        except Exception, e:
            print '->\t Error pylast: ', e
        else:
                if 'urls' not in release:
                    release['urls'] = {}
                release['urls']['Last.fm'] = [lastfm_url]

                if lastfm_abstract:
                    release_group.abstract = {'content':strip_tags(lastfm_abstract), 'lang':'en', 'provider':'Last.fm', 'url':lastfm_url}

                if lastfm_cover:
                    release['cover'] = lastfm_cover

        # TODO: when to save? when failed do we retry?
        release_group.cache_state['lastfm']    = [1,datetime.utcnow()]
        release_group.save()
    return release_group

def create_mb_artist(mbid):
    """
    Fetch basic metadata and store it as a CachedArtist document.

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return: a CachedArtist object with basic MusicBrainz data
    """
    q = ws.Query(mb_webservice)
    try:
        mmda_logger('mb','request','artist',mbid)
        mb_artist = q.getArtistById(mbid, ExtendedArtistIncludes())
        mmda_logger('mb','result', 'artist',mb_artist.name)
    except ws.WebServiceError, e:
        # TODO: hard error page here
        # TODO: 404 not found redirect to different page? conditional?
        print '[!] ->\tMusicBrainz artist ERROR:', e
    else:
        artist                      = CachedArtist.get_or_create(mbid)
        artist                      = populate_artist_mb(artist, mb_artist)
        artist.cache_state['mb']    = [1,datetime.utcnow()]
        artist.save()
        mmda_logger('db','store','artist',artist.name)

        # since we have some basic release data fetched with artist, store it
        create_shallow_releases_mb(mbid, mb_artist.getReleases())

        # TODO: think about genres and origin - fetch from freebase(?)
        # freebase.mqlread({"type":"/music/artist", "limit": 1, "key": [{"namespace" : '/authority/musicbrainz',"value" : '579ef111-19dd-4ae8-ad50-d5fa435472b9'}], "genre":[], "origin":None} )
    return artist

def create_shallow_releases_mb(artist_mbid, mb_releases):
    """
    Create CachedReleaseGroup documents using basic MusicBrainz data fetched with artist.

    @param artist_mbid: a string containing a MusicBrainz ID of an artist
    @param mb_releases: a list of musicbrainz2.model.Release objects
    """

    # magical place where all data is cached/processed before database commit
    there_will_be_dragons = {}

    for mb_release in mb_releases:
        group_mbid      = extractUuid(mb_release.releaseGroup.id)
        release_mbid    = extractUuid(mb_release.id)

        # its ugly, but we fill this only once (place for future improvements)
        if group_mbid not in there_will_be_dragons:
            release_group                       = {}
            release_group['_id']                = group_mbid
            release_group['artist_mbid']        = artist_mbid
            release_group['title']              = mb_release.releaseGroup.title
                                                # small fix: in some rare cases, ReleaseGroup at Musicbrainz has no 'type' property
            release_group['release_type']       = decruft_mb(mb_release.releaseGroup.type) if mb_release.releaseGroup.type else 'Other'
            release_group['releases']           = {}
            there_will_be_dragons[group_mbid]   = release_group
        else:
            release_group = there_will_be_dragons[group_mbid]

        # store only basic information about release event
        mb_release_events = []
        for mb_event in mb_release.getReleaseEvents():
            event = {}
            if mb_event.date:
                event['date']    = mb_event.date
            if mb_event.format:
                event['format']  = decruft_mb(mb_event.format)
            if mb_event.country:
                event['country'] = mb_event.country
            if event:
                mb_release_events.append(event)

        release_group['releases'][release_mbid] = {
                'title':mb_release.title,
                'tracks_count':mb_release.tracksCount,
                'release_events':mb_release_events,
                'cache_state':{'mb':[1,datetime.utcnow()]}
                }

        # primary release is the one with earliest release date (place for future improvements)
        mb_earliest_release_date = mb_release.getEarliestReleaseEvent().getDate() if mb_release.getEarliestReleaseEvent() else None
        if 'primary' not in release_group or release_group['primary'][1] == None or mb_earliest_release_date < release_group['primary'][1]:
            release_group['primary'] = [release_mbid, mb_earliest_release_date]

    # TODO: optimize? remove? wtf
    old_cached_release_groups = db.view('artists/release_groups', key=artist_mbid)
    for group in old_cached_release_groups:
        CachedReleaseGroup.get(group['id']).delete()

    for release_group in there_will_be_dragons.itervalues():
        #cached_release_group = CachedReleaseGroup.get_or_create(group_mbid)
        cached_release_group = CachedReleaseGroup.wrap(release_group)
        cached_release_group.cache_state['mb'] = [1,datetime.utcnow()]
        cached_release_group.save()
        mmda_logger('db','store','release_group',cached_release_group.title)

def populate_deep_release_mb(release_group,release_mbid):
    """
    Make sure ReleaseGroup contains additional, detailed information about specified release.

    @param release_group: a CachedReleaseGroup object
    @param release_mbid:  a string containing a MusicBrainz ID of a release

    @return: a verified/updated CachedReleaseGroup object
    """
    release = release_group.releases[release_mbid]
    if release['cache_state']['mb'][0] == 1:
        q = ws.Query(mb_webservice)
        # TODO: remove unused includes
        inc = ws.ReleaseIncludes(
                tracks=True,
                trackRelations=True,
                artistRelations=True,
                releaseRelations=True,
                urlRelations=True,
                )
        try:
            mmda_logger('mb','request','release',release_mbid)
            mb_release  = q.getReleaseById(release_mbid, inc)
            mmda_logger('mb','result','release',mb_release.title)
        except ws.WebServiceError, e:
            # TODO: hard error here
            print '[!] ->\tMusicBrainz release ERROR:', e
        else:
            # make sure mbid of an artist is present
            if 'artist_mbid' not in release_group:
                release_group.artist_mbid = extractUuid(mb_release.artist.id)

            # TRACK LISTING
            # TODO: think about duration representation here
            tracks = []
            for mb_track in mb_release.tracks:
                track = {'title':mb_track.title, 'mbid':extractUuid(mb_track.id)}
                if mb_track.duration:
                    track['duration'] = humanize_duration(mb_track.duration)
                tracks.append(track)
            release['tracks'] = tracks

            # URL relations
            urls = {}
            for relation in mb_release.getRelations(m.Relation.TO_URL):
                relation_type = decruft_mb(relation.type)
                if relation_type not in urls:
                    urls[relation_type] = []
                urls[relation_type].append(relation.targetId)
            # urls is used in many places, so its handy to have it ready
            release['urls'] = urls

            # CREDIT relations
            credits = [{'type':decruft_mb(r.type), 'mbid':extractUuid(r.targetId), 'name':r.target.name} for r in mb_release.getRelations(m.Relation.TO_ARTIST)]
            if credits:
                release['credits'] = credits

            # MULTI-DISC-RELEASE information
            remasters = []
            for relation in mb_release.getRelations(m.Relation.TO_RELEASE):
                relation_type = decruft_mb(relation.type)
                linked_release = {'mbid':extractUuid(relation.targetId), 'title':relation.target.title}

                if relation_type == 'PartOfSet':
                    if relation.direction == 'backward':
                        release['set_prev'] = linked_release
                    else:
                        release['set_next'] = linked_release

                elif relation_type == 'Remaster':
                    if relation.direction == 'backward':
                        remasters.append(linked_release)
                    else:
                        release['remaster_of'] = linked_release
            if remasters:
                release['remasters'] = remasters

            release['cache_state']['mb'] = [2,datetime.utcnow()]
            release_group = perform_cover_lookup_on_mb_data(release_group, release_mbid)
            release_group.save()
            mmda_logger('db','store','release',release['title'])
    else:
        mmda_logger('db','present','release',release['title'])

    return release_group

def decruft_mb(string):
    """
    Remove overhead from MusicBrainz data.

    @param string: a string containing MusicBrainz namespace prefix

    @return: a string without MusicBrainz namespace prefix
    """
    if string:
        return string.split('#')[-1]
    else:
        return string

def humanize_duration(millis):
    """
    Convert miliseconds to human-readable format.

    @param miliseconds: a duration value in miliseconds

    @return: a string with human-readable format.
    """
    hours = millis / 3600000
    mins  = (millis - hours * 3600000) / 60000
    secs  = (millis - hours * 3600000 - mins * 60000) / 1000
    if hours:
        return "%(hours)d:%(mins)02d:%(secs)02d" % locals()
    else:
        return "%(mins)d:%(secs)02d" % locals()

def perform_cover_lookup_on_mb_data(release_group, release_mbid):
    """
    Look for an Amazon or (a preffered) CoverArt relationship and store URL in 'cover' field.

    'CoverArtLink' relation is removed, but 'AmazonASIN' stays since it may serve other purpose.

    @param release_group: a CachedReleaseGroup object
    @param release_mbid:  a string containing a MusicBrainz ID of a release

    @return: a verified/updated CachedReleaseGroup object
    """
    release = release_group.releases[release_mbid]
    cover_url = False

    if 'cover' not in release and 'urls' in release:
        for link_type,links in release['urls'].iteritems():

            if link_type == 'CoverArtLink':
                cover_url = links[0]
                del release['urls']['CoverArtLink']
                break

            elif link_type == 'AmazonAsin':
                asin = links[0].split('/')[-1]
                cover_url = "http://images.amazon.com/images/P/%s.01.MZZZZZZZ.jpg" % asin
    # TODO: handle jamendo (example: /artist/pornophonique/release/8-bit-lagerfeuer/77baaaf6-8128-400e-aee7-0e9a6ca79692/ )
    if cover_url:
        release['cover'] = cover_url

    return release_group

def populate_artist_mb(artist, mb_artist):
    """
    Process data from MusicBrainz and store it in dedicated structures of CachedArtist.

    @param artist: a CachedArtist object
    @param mb_artist: a musicbrainz2.model.Artist object

    @return: a populated CachedArtist object
    """
    artist.artist_type          = decruft_mb(mb_artist.type)
    artist.name                 = mb_artist.name
    artist.sort_name            = mb_artist.sortName

    if mb_artist.disambiguation:
        artist.disambiguation   = mb_artist.disambiguation
    if mb_artist.aliases:
        artist.aliases          = [a.value for a in mb_artist.aliases]

    if mb_artist.beginDate or mb_artist.endDate:
        artist.dates = {}
    if mb_artist.beginDate:
        artist.dates['from']    = mb_artist.beginDate
    if mb_artist.endDate:
        artist.dates['to']      = mb_artist.endDate

    # urls are stored in dict with lists as values (there can be many of the same type)
    urls = {}
    for relation in mb_artist.getRelations(m.Relation.TO_URL):
        relation_type = decruft_mb(relation.type)
        if relation_type not in urls:
            urls[relation_type] = []
        urls[relation_type].append(relation.targetId)
    if urls:
        artist.urls = urls

    # on the other hand, memberships and collaborations are stored in lists of dicts ;-)
    members             = []
    member_of           = []
    collaborations      = []
    collaboration_of    = []

    for relation in mb_artist.getRelations(m.Relation.TO_ARTIST):
        relation_type = decruft_mb(relation.type)
        if relation_type == 'MemberOfBand':
            member_info = {
                    'name':relation.target.name,
                    'mbid':extractUuid(relation.targetId),
                    'from':relation.beginDate,
                    'to':relation.endDate
                    }
            if relation.direction == 'backward':
                members.append(member_info)
            else:
                member_of.append(member_info)
        elif relation_type == 'Collaboration':
            member_info = {
                    'name':relation.target.name,
                    'mbid':extractUuid(relation.targetId)
                    }
            if relation.direction == 'backward':
                collaboration_of.append(member_info)
            else:
                collaborations.append(member_info)

    if members:
        artist.members          = members
    if member_of:
        artist.member_of        = member_of
    if collaborations:
        artist.collaborations   = collaborations
    if collaboration_of:
        artist.collaboration_of = collaboration_of
    return artist

def populate_abstract(artist_or_releasegroup):
    """
    Populate CachedArtist or CachedRleaseGroup with short abstract.

    High-level API aimed to replace populate_*_lastfm

    @param artist_or_releasegroup: a CachedArtist or CachedReleaseGroup object
    @return: a CachedArtist or CachedReleaseGroup object
    """
    if 'abstract' not in artist_or_releasegroup:
        abstract = get_abstract_from_dbpedia(artist_or_releasegroup)
        # TODO: add other abstract sources here
        if abstract:
            artist_or_releasegroup.abstract = abstract
            artist_or_releasegroup.cache_state[abstract['provider']]  = [1,datetime.utcnow()]
            artist_or_releasegroup.save()
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
    if 'Wikipedia' not in artist_or_releasegroup.cache_state:
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
                mmda_logger('wiki','request','abstract',wiki_resource)
                # TODO: timeout?
                sparql_result = session.default_store.execute_sparql(sparql_query) # TODO: error handling
                mmda_logger('wiki','result','found',len(sparql_result['results']['bindings']))
                if sparql_result['results']['bindings']:
                    abstract = {'content':unicode(sparql_result['results']['bindings'][0]['abstract']), 'url':wiki_url, 'lang':wiki_lang, 'provider':'Wikipedia'}
                    # TODO: add cache_status dbpedia
            except Exception:
                #artist_or_releasegroup.wikipedia = {'abstract':'fail dawg'}
                # TODO: handle it?
                print '[!] ->\tDbpedia abstract fetch ERROR:', e
    return abstract

# HELPERS

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

def lastfm_get_similar_optimized(lastfm_artist,limit=10):
    """
    Get similar artists from last.fm API in optimized way.

    Currently the only way to get mbids of such artists in pylast is item.get_mbid() method,
    which invokes 'artist.getInfo()' API method -- this is an overhead of one additional http request for each similar artist.
    It is redundant, since mbids are already in obtained XML, but pylast architecture ignores it atm.
    This method is a necessary workaround.

    @param lastfm_artist: a pylast.Artist object
    @param limit: number of similar artist to get

    @return:  a dictionary with artist name, score and mbid
    """
    params = lastfm_artist._get_params()
    params['limit'] = pylast._unicode(limit)
    doc = lastfm_artist._request('artist.getSimilar', True, params)
    names = pylast._extract_all(doc, "name")
    mbids = pylast._extract_all(doc, "mbid")
    matches = pylast._extract_all(doc, "match")
    similar_artists = []
    for i in range(0, len(names)):
        if mbids[i]:
            similar_artists.append({'name':names[i], 'score':int(float(matches[i])*100), 'mbid':mbids[i]})
    # TODO: catch and store images?
    return similar_artists


class ExtendedArtistIncludes(ws.IIncludes):
    """
    Drop-in replacement of musicbrainz2.webservice.ArtistIncludes object.

    ArtistIncludes does not support 'release-events' include parameter. This class is a workaround.
    """
    def createIncludeTags(self):
        return ['url-rels', 'sa-Official', 'artist-rels', 'release-groups', 'aliases', 'release-events','counts']

