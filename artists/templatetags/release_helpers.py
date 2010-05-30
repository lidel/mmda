# -*- coding: utf-8
import re
import random

from django import template
from django.conf import settings
from django.template.defaultfilters import slugify, urlencode, force_escape, safe
from unidecode import unidecode

from musicbrainz2.utils import extractUuid
from datetime import datetime

register = template.Library()

@register.filter
def inclusivedictsort(list, key):
    """
    Sort list of dicts by specified field.

    Put the ones without such field at the end. (generic dictsort removed such from sorted list)
    The main use is to have releases sorted descending by year.

    @param list: a list of dicts
    @param key: a dict key to sort the list by

    @return: a sorted list of dicts
    """
    decorated = [(i[key] if key in i else '', i) for i in list]
    decorated.sort()
    decorated.reverse()
    return [item[1] for item in decorated]
inclusivedictsort.is_safe = False

@register.filter
def trim(value, arg=4):
    """
    Leave only specified number of characters (default is 4).
    """
    if value:
        return value[:arg]
    else:
        return value
trim.is_safe = True

@register.filter
def mbid(value):
    """
    Extract mbid from url.
    """
    return extractUuid(value)
trim.is_safe = True

@register.filter
def slugify2(value):
    """
    Thin wrapper around default slugify to handle extreme unicode cases (such as japanese etc)
    using Unidecode library (http://pypi.python.org/pypi/Unidecode/0.04.1).

    @param value: a string

    @return: a SEO-friendly URL-ish string
    """
    return slugify(unidecode(value))
slugify2.is_safe = True

@register.filter
def spacecamel(value):
    """
    Add spaces to a camel case string.

    @param value: a string

    @return: an updated string
    """
    # TODO: make it smart
    if value != 'IMDb':
        return re.sub('((?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z]))', ' ', value).strip()
    else:
        return value
spacecamel.is_safe = True

@register.filter
def percentage(fraction, population=1):
    """
    Return 'fraction' represented as percentage of 'population'

    @param fraction: a numerical value
    @param population: a numerical value representing 100%

    @return: a string with percentage representation
    """
    try:
        return "%.0f%%" % ((float(fraction) / float(population)) * 100)
    except ValueError:
        return ''
percentage.is_safe = True

@register.filter
def dict_get(dict, key):
    """
    Return value under specified key.

    usage: {{dictionary|dict_get:var}}
    """
    if key in dict:
        return dict[key]
    else:
        return None


# TODO: coralize (adds .nyud.net to links)
@register.filter
def coralize(value):
    """
    Append .nyud.net to domain in URL when in production mode
    """
    if settings.DEBUG:
        return value
    else:
        url = value.split('/')
        url[2] = url[2]+'.nyud.net'
        return '/'.join(url)
coralize.is_safe = True

@register.filter
def iso2date(str):
    """
    Parse string with date and return Python datetime.

    @param str: a string

    @return: a datetime object
    """
    try:
        return datetime.strptime(str,'%Y-%m-%dT%H:%M:%SZ')
    except:
        return None
spacecamel.is_safe = True

@register.filter
def addtypography(string):
    """
    Add typographic eye-candy to a string.

    @param value: a string

    @return: an updated string
    """
    try:
        html = force_escape(string)
        html = html.replace('&amp;','<span class="amp">&amp;</span>')
        return safe(html)
    except Exception, e:
        print e 
        return string
addtypography.is_safe = True

@register.inclusion_tag('artists/tags/abstract.html')
def abstract_for(entity):
    """
    Node that displays Cached*.abstract
    """
    return {'entity': entity}

@register.inclusion_tag('artists/tags/urls.html')
def urls_for(entity, mbid):
    """
    Node that displays Cached*.urls
    """
    if 'doc_type' in entity: # and entity.doc_type == 'CachedArtist':
        entity_type = 'artist'
    else:
        entity_type = 'release'

    return {'entity': entity, 'entity_type':entity_type, 'mbid': mbid}

@register.inclusion_tag('artists/tags/tags.html')
def tag_cloud_for(tags):
    """
    Node that displays Cached*.tags
    """
    return {'tags': tags}
