# -*- coding: utf-8
from django.shortcuts import render_to_response
#from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse

#from mmda.artists.templatetags.release_helpers import slugify2
from mmda.engine.tag import get_populated_tag

def show_tag(request, tag_id):
    """
    Show page with tag.

    @param tag_id: a string containing a tag ID

    @return: a rendered tag page
    """
    # TODO: wrap Http400 over show_tag with proper message if cache_state == False
    tag = get_populated_tag(tag_id)

    # TODO: add seo check with get_normalized_tag -- move it here?
    return render_to_response('tags/show_tag.html', locals())

