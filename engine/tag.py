# -*- coding: utf-8

from datetime import datetime
from django.conf import settings
from mmda.engine.utils import mmda_logger
from mmda.tags.models import CachedTag
from couchdbkit.resource import ResourceNotFound
from mmda.artists.templatetags.release_helpers import slugify2

#from mmda.engine.artist import get_basic_artist

# TODO: implement
from mmda.engine.api.lastfm import populate_tag_lastfm


def get_populated_tag(tag_string):
    """
    Return populated object required by mmda.tags.show_tag

    Designed to be stored in database only when populated by anything.

    @param tag_id: a string containing an ID of a tag

    @return: a CachedTag object
    """
    tag = CachedTag.get_or_create(slugify2(tag_string))
    tag = populate_tag_lastfm(tag)
    # TODO: abstract from lastfm?

    tag.save_any_changes()

    return tag

#def get_normalized_tag(tag):
#    """
#    Make some optimizations on tag string.
#
#    @param tag: a string containing a tag
#
#    @return: a string containing an optimized tag
#    """
#    return tag.strip().lower()

