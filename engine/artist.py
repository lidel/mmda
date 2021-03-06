# -*- coding: utf-8
from musicbrainz2.webservice import WebServiceError
from musicbrainz2.model import Relation
from musicbrainz2.utils import extractUuid
from mmda.engine.api.musicbrainz import mb_query, MB_ARTIST_INCLUDES

from datetime import datetime
from random import shuffle

from django.conf import settings
from couchdbkit.resource import ResourceNotFound
from couchdbkit.ext.django.loading import get_db
from mmda.artists.models import CachedArtist, CachedReleaseGroup
from mmda.engine.utils import mmda_logger, decruft_mb
from mmda.engine.abstract import populate_abstract
from mmda.engine.api.lastfm import populate_artist_lastfm


"""
    Short story about decoupled design of mmda.engine

    Why functions clearly connected to Cached* documents
    are separated from models, eg. mmds.artists.models?

    Two reasons:
    - Avoiding circural import of Cached* which caused errors (ok, it is a bad design anyway and silly excuse)
    - Decoupling. Each API has dedicated file which makes future maintenance easier.
    - Object-oriented approach would make things unnecessarily complicated here, IMO.

    We can always go OOP in future, but this way it is easier to extend atm.
"""

def get_populated_artist(mbid):
    """
    Make sure artist document is present and contains data required by mmda.artists.show_artist

    @param mbid:    a string containing a MusicBrainz ID of an artist

    @return: a CachedArtist object containing required minimal data set
    """
    artist = get_basic_artist(mbid)

    artist = populate_abstract(artist)
    artist = populate_artist_lastfm(artist)

    artist.save_any_changes()

    return artist

def get_artist_primary_releases(mbid):
    """
    Get a list of official, primary releases by an artist specified by MusicBrainzID.

    @param mbid:    a string containing a MusicBrainz ID of an artist

    @return: a list of dicts with basic primary release meta-data
    """
    view = get_db('artists').view('artists/release_groups', key=mbid)
    primary_releases = [group['value'] for group in view.all()]

    return primary_releases

def get_artist_best_pictures(mbid):
    """
    Get artist pictures required by mmda.artists.show_artist

    @param mbid:    a string containing a MusicBrainz ID of an artist

    @return: a list of dicts with artist picture meta-data
    """
    view = get_db('pictures').view('pictures/best_pictures', key=mbid, limit=4)
    best_pictures = [group['value'] for group in view.all()]

    shuffle(best_pictures)

    return best_pictures

def get_recent_artists():
    """
    Get recently cached artists required by mmda.artists.index

    @return: a list of dicts with artist name and mbid
    """
    view = get_db('artists').view('artists/recent_artists', limit=10, descending=True)
    recent_artists = [group['value'] for group in view.all()]

    return recent_artists

def get_artist_cache_state(mbid):
    """
    Get artist cache status required by mmda.artists.show_artist

    @param mbid:    a string containing a MusicBrainz ID of an artist

    @return: a list of dicts with artist picture meta-data
    """
    cache_states = []
    # TODO: one big database? how would that work?
    databases = ['artists','pictures','videos','news']

    for db in databases:
        try:
            doc = get_db(db).get(mbid)
            if doc.has_key('cache_state') and doc['cache_state']:
                cache_states.append({db:doc['cache_state']})
        except:
            continue

    return cache_states

def get_basic_artist(mbid):
    """
    Make sure basic artist document is present and contains required data.

    @param mbid:    a string containing a MusicBrainz ID of an artist

    @return: a CachedArtist object containing required minimal data set
    """
    #TODO: handle Various Artists' artist (VARIOUS_ARTISTS_ID)
    try:
        artist = CachedArtist.get(mbid)
        mmda_logger('db','present',artist._doc_type, artist.get_id)
    except ResourceNotFound:
        artist = _create_mb_artist(mbid)
    return  artist

def _create_mb_artist(mbid):
    """
    Fetch basic metadata and store it as a CachedArtist document.

    @param mbid: a string containing a MusicBrainz ID of an artist

    @return: a CachedArtist object with basic MusicBrainz data
    """
    try:
        t = mmda_logger('mb','request','artist',mbid)
        mb_artist = mb_query.getArtistById(mbid, MB_ARTIST_INCLUDES)
        mmda_logger('mb','result', 'artist',mb_artist.name,t)
    except WebServiceError, e:
        # TODO: hard error page here
        # TODO: 404 not found redirect to different page? conditional?
        # TODO:  HTTP Error 503: Service Temporarily Unavailable -> special case:  please wait few seconds and hit F5
        mmda_logger('mb-artist','ERROR',e)
        raise e
    else:
        artist                      = CachedArtist.get_or_create(mbid)
        artist                      = _populate_artist_mb(artist, mb_artist)
        artist.cache_state['mb']    = [1,datetime.utcnow()]
        artist.save()
        mmda_logger('db','store',artist)

        # since we have some basic release data fetched with artist, store it
        _create_shallow_releases_mb(mb_artist)

        # TODO: think about genres and origin - fetch from freebase(?)
        # freebase.mqlread({"type":"/music/artist", "limit": 1, "key": [{"namespace" : '/authority/musicbrainz',"value" : '579ef111-19dd-4ae8-ad50-d5fa435472b9'}], "genre":[], "origin":None} )
    return artist

def _populate_artist_mb(artist, mb_artist):
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
    for relation in mb_artist.getRelations(Relation.TO_URL):
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

    for relation in mb_artist.getRelations(Relation.TO_ARTIST):
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

def _create_shallow_releases_mb(mb_artist):
    """
    Create CachedReleaseGroup documents using basic MusicBrainz data fetched with artist.

    @param mb_artist: a musicbrainz2.model.Artist object
    """
    mb_releases = mb_artist.getReleases()
    artist_mbid = extractUuid(mb_artist.id)

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
            release_group['artist_name']        = mb_artist.name
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

    # just to make sure no old data is left..
    old_cached_release_groups = get_db('artists').view('artists/release_groups', key=artist_mbid)
    for group in old_cached_release_groups:
        del get_db('artists')[group['id']]

    for release_group in there_will_be_dragons.itervalues():
        cached_release_group = CachedReleaseGroup.wrap(release_group) # TODO: think if wrap is the best way of dealing with this
        cached_release_group.cache_state['mb'] = [1,datetime.utcnow()]
        cached_release_group.save() # TODO: add try in case of ResourceConflict? 
        mmda_logger('db','store', cached_release_group)

