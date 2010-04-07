# -*- coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from mmda.artists.models import CachedArtist, CachedReleaseGroup
from couchdbkit.ext.django.loading import get_db
from couchdbkit.resource import ResourceNotFound
import musicbrainz2.webservice as ws
import musicbrainz2.model as m
from musicbrainz2.utils import extractUuid, extractFragment
from datetime import datetime
import re
import pylast
import surf
#
import time
from django.conf import settings


#from django.template.defaultfilters import slugify
from mmda.artists.templatetags.release_helpers import slugify2
from django.core.urlresolvers import reverse

    #return HttpResponse("%s" % (results,))

# TODO: check if safe as global
db = get_db('artists')
mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)
if settings.DEBUG:
    t1 = time.time()

def index(request):
    return render_to_response('artists/index.html', locals())

def show_artist(request, uri_artist, mbid):
    """
    Show page of an artist specified by mbid.
    """

    artist = initiate_artist(mbid)

    # TODO: check if lasfm stuff is only used here
    artist = populate_artist_lastfm(artist)
    artist = populate_dbpedia(artist)

    unsorted_release_groups = db.view('artists/release_groups', key=mbid)

    release_groups = [release['value'] for release in unsorted_release_groups.all()]

    # basic SEO check
    artist_seo_name = slugify2(artist.name)
    if uri_artist == artist_seo_name:
        return render_to_response('artists/show_artist.html', locals())
    else:
        return HttpResponsePermanentRedirect(reverse('show-artist', args=(artist_seo_name, mbid)))

def show_release(request, uri_artist, uri_release, mbid):
    """
    Show page of a release specified by mbid.
    """
    release_group   = initiate_release(mbid)
    artist          = initiate_artist(release_group.artist_mbid)
    release_group   = populate_deep_release_mb(release_group,mbid)
    release         = release_group.releases[mbid]

    release_group   = populate_dbpedia(release_group)
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

    Return CachedArtist
    """
    try:
        artist = CachedArtist.get(mbid)
    except ResourceNotFound:
        artist = create_mb_artist(mbid)
    return  artist

def initiate_release(mbid):
    """
    Make sure release document is present and contains required data.

    Return CachedReleaseGroup
    """
    release_group   = CachedReleaseGroup.view('artists/releases',include_docs=True, key=mbid).one()
    #if True:
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
    Fetch last.fm data and append to CachedArtist document.
    """
    if artist.cache_state['lastfm'][0] == 0:
        lastfm = pylast.get_lastfm_network(api_key = settings.LASTFM_API_KEY)
        try:
            mmda_logger('last','request','artist',artist._id)
            lastfm_artist = lastfm.get_artist_by_mbid(artist._id)
            mmda_logger('last','result','artist',artist._id)
            # TODO: run there in parallel (?)
            mmda_logger('last','request','images',artist._id)
            lastfm_images = images = [ {'full':i.sizes.original, 'square':i.sizes.largesquare, 'big':i.sizes.extralarge, 'url':i.url,'title':i.title} for i in lastfm_artist.get_images(limit=5)]
            mmda_logger('last','result','images',artist._id)
            lastfm_url    = lastfm_artist.get_url()
            # we get similar artists from lastfm database, but only those with mbid (omg, omg)
            # TODO: think about numbers of fetched things
            mmda_logger('last','request','similar',artist._id)
            lastfm_similar  = lastfm_get_similar_optimized(lastfm_artist,limit=10)
            mmda_logger('last','result','similar',artist._id)
            mmda_logger('last','request','tags',artist._id)
            lastfm_tags     = [(t.item.name.lower(), int(t.weight)) for t in lastfm_artist.get_top_tags(limit=10)]
            mmda_logger('last','result','tags',artist._id)
        except Exception, e:
            print 'Error pylast:', e
        else:
            # TODO: make it compatible with tags imported from mb (TODO2: add tags from MusicBrainz)

            # TODO: remove random?
            import random
            random.shuffle(lastfm_tags)

            artist.tags                     = lastfm_tags
            artist.similar                  = lastfm_similar
            artist.urls['Last.fm']          = [lastfm_url]
            artist.images['lastfm']         = lastfm_images
            mmda_logger('db','store','[last.fm data] artist',artist._id)
        # if fail, store state too -- to avoid future attempts
        artist.cache_state['lastfm']    = [1,datetime.utcnow()]
        artist.save()
    return artist

def create_mb_artist(mbid):
    """
    Fetch basic metadata and store as a CachedArtist document.
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
    Create CachedReleaseGroup documents with basic release information.
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
    Fill ReleaseGroup.releases[release_mbid] with MusicBrainz details such as track listing and release relationships.
    """
    #release_group = CachedReleaseGroup.get_or_create(mbid)

    # now fetch details of included releases
    #        counts=True,
    #        releaseEvents=True,
    #        releaseGroup=True,
    #        labels=True
    #        artist=True,
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
            if urls:
                release['urls']         = urls

            # CREDIT relations
            credits = [{'type':decruft_mb(r.type), 'mbid':extractUuid(r.targetId), 'name':r.target.name} for r in mb_release.getRelations(m.Relation.TO_ARTIST)]
            if credits:
                release['credits']      = credits

            # MULTI-DISC-RELEASE information
            # TODO: add remaster handling
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

            release = populate_cover_url(release) # TODO: move level up, after/if advanced cover lookup is added (lolwut)

            release['cache_state']['mb'] = [2,datetime.utcnow()]
            release_group.save()
            mmda_logger('db','store','release',release['title'])
    else:
        mmda_logger('db','present','release',release['title'])

    return release_group

# TODO: remove legacy cruft_type
def decruft_mb(string,cruft_type=0):
    """
    Remove overhead from MusicBrainz data.
    """
    if string:
        return string.split('#')[-1]
    else:
        return string

def humanize_duration(millis):
    """
    Convert miliseconds to human-readable format.
    """
    hours = millis / 3600000
    mins  = (millis - hours * 3600000) / 60000
    secs  = (millis - hours * 3600000 - mins * 60000) / 1000
    if hours:
        return "%(hours)d:%(mins)02d:%(secs)02d" % locals()
    else:
        return "%(mins)d:%(secs)02d" % locals()

def populate_cover_url(release):
    """
    Find cover artwork using Amazon or (preffered) CoverArt relationship and store URL in 'cover' field.

    CoverArtLink relation is removed, but AmazonASIN stays since it may serve other purpose.
    """
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
    # TODO: additional/fallback cover lookoop here
    if not cover_url:
        # TODO: make it smart
        release['cover'] = 'http://www.cornielyrics.org.nyud.net/images/jewelcase.png'
    if cover_url:
        release['cover'] = cover_url
    return release

def populate_artist_mb(artist, mb_artist):
    """
    Process data from MusicBrainz and store it in dedicated structures of CachedArtist.
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

def populate_dbpedia(artist_or_releasegroup):
    """
    Populate CachedArtist or CachedRleaseGroup with abstract from wikipedia (if present).
    """
    # if artist_or_releasegroup is ReleaseGroup, we look for release with wikipedia URL
    # TODO: check performance, and if better - replace in other parts
    # TODO: DRY: refactor
    # TODO: make compatible with multiple abstract sources
    if 'wiki' not in artist_or_releasegroup.cache_state:
        wiki_resource = None
        if 'releases' in artist_or_releasegroup:
            for release in artist_or_releasegroup['releases'].itervalues():
                if 'urls' in release  and 'Wikipedia' in release['urls']:
                    for url in release['urls']['Wikipedia']:
                        print wiki_resource
                        raped_url     = url.split('/')
                        wiki_resource = raped_url[-1]
                        wiki_lang     = raped_url[2].split('.')[0]
                        wiki_url      = url
                        if wiki_lang == 'en':
                            break
        # TODO: fix WARNING:ReaderPlugin:cjson not available, falling back on slower simplejson
        # TODO: move to release_group level?
        elif 'urls' in artist_or_releasegroup and 'Wikipedia' in artist_or_releasegroup['urls']:
            for url in artist_or_releasegroup['urls']['Wikipedia']:
                raped_url     = url.split('/')
                wiki_resource = raped_url[-1]
                wiki_lang     = raped_url[2].split('.')[0]
                wiki_url      = url
                if wiki_lang == 'en':
                    break

        if wiki_resource:
            store = surf.Store(reader = "sparql_protocol", endpoint = "http://dbpedia.org/sparql")
            session = surf.Session(store)
            sparql_query = "SELECT ?abstract WHERE {{ <http://dbpedia.org/resource/%s> <http://dbpedia.org/property/abstract> ?abstract FILTER langMatches( lang(?abstract), '%s') } }" % (wiki_resource, wiki_lang)
            try:
                mmda_logger('wiki','request','abstract',wiki_resource)
                # TODO: timeout?
                sparql_result = session.default_store.execute_sparql(sparql_query) # TODO: error handling
                mmda_logger('wiki','result','found abstracts',len(sparql_result['results']['bindings']))
                if sparql_result['results']['bindings']:
                    artist_or_releasegroup.abstract = {'content':unicode(sparql_result['results']['bindings'][0]['abstract']), 'url':wiki_url, 'lang':wiki_lang, 'provider':'Wikipedia'}
                    artist_or_releasegroup.cache_state['wiki'] = [1,datetime.utcnow()]
                    artist_or_releasegroup.save()
                    # TODO: add cache_status dbpedia
            except Exception:
                #artist_or_releasegroup.wikipedia = {'abstract':'fail dawg'}
                # TODO: handle it?
                pass
    return artist_or_releasegroup

# HELPERS

def lastfm_get_similar_optimized(lastfm_artist,limit=10):
    """
    Get similar artists from last.fm API in optimized way.

    Currently the only way to get mbids of such artists in pylast is item.get_mbid() method,
    which invokes 'artist.getInfo()' API method -- this is an overhead of one additional http request for each similar artist.
    It is redundant, since mbids are already in obtained XML, but pylast architecture ignores it atm.
    This method is a necessary workaround (very easy thanks to Pythons architecture ;-) ).
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

def mmda_logger(entity, action, object_type, object_id):
    """
    Simple stdout printer that makes debugging easier.
    """
    if settings.DEBUG:
        global t1
        arrows = {'store':'=>','present':'<=','request':'->', 'result':'<-'}
        if action == 'request':
            t1 = time.time()
        if action == 'result':
            print "\t(%s-%s)\t%s   %.2fs %s:\t\t'%s'" % (entity, action, arrows[action], (time.time()-t1) ,object_type, object_id)
        else:
            print "\t(%s-%s)\t%s         %s:\t\t'%s'" % (entity, action, arrows[action], object_type, object_id)
