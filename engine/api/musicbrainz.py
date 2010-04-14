# -*- coding: utf-8
from django.conf import settings
import musicbrainz2.webservice as ws

class ExtendedArtistIncludes(ws.IIncludes):
    """
    Drop-in replacement of musicbrainz2.webservice.ArtistIncludes object.

    ArtistIncludes does not support 'release-events' include parameter. This class is a workaround.
    """
    def createIncludeTags(self):
        return ['url-rels', 'sa-Official', 'artist-rels', 'release-groups', 'aliases', 'release-events','counts']


mb_webservice = ws.WebService(host=settings.MB_WEBSERVICE_HOST)
mb_query = ws.Query(mb_webservice)

MB_ARTIST_INCLUDES  = ExtendedArtistIncludes()
MB_RELEASE_INCLUDES = ws.ReleaseIncludes(
                        tracks=True,
                        trackRelations=True,
                        artistRelations=True,
                        releaseRelations=True,
                        urlRelations=True,
                        )

