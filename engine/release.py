# -*- coding: utf-8
import musicbrainz2.webservice as ws
import musicbrainz2.model as m

from datetime import datetime

from django.conf import settings
from couchdbkit.resource import ResourceNotFound
from couchdbkit.ext.django.loading import get_db
from musicbrainz2.utils import extractUuid


from mmda.artists.models import CachedReleaseGroup
from mmda.engine.abstract import populate_abstract
from mmda.engine.utils import mmda_logger, decruft_mb, humanize_duration
from mmda.engine.api.lastfm import populate_release_lastfm

# TODO: DRY -> move to settings?
mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)


def get_populated_releasegroup_with_release(mbid):
    """
    Return populated objects required by mmda.artists.show_release

    @param mbid: a string containing a MusicBrainz ID of a release

    @return:  a tuple: (release group, release)
    """

    release_group   = get_basic_release(mbid)
    release_group   = populate_deep_release_mb(release_group, mbid)

    # used only by mmda.artists.show_release
    release_group   = populate_abstract(release_group)
    release_group   = populate_release_lastfm(release_group, mbid)

    return (release_group, release_group.releases[mbid])

def get_basic_release(mbid):
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
            mmda_logger('mb-release','ERROR',e)
            raise Http500
        else:
            get_basic_artist(artist_mbid)
            release_group = CachedReleaseGroup.view('artists/releases',include_docs=True, key=mbid).one()
    return release_group

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
            mmda_logger('mb-release','ERROR',e)
            raise Http500
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
            release_group = _perform_cover_lookup_on_mb_data(release_group, release_mbid)
            release_group.save()
            mmda_logger('db','store','release',release['title'])
    else:
        mmda_logger('db','present','release',release['title'])

    return release_group

def _perform_cover_lookup_on_mb_data(release_group, release_mbid):
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

