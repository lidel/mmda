# -*- coding: utf-8
from django import template
from musicbrainz2.utils import extractUuid
from django.template.defaultfilters import slugify, urlencode, escape
import re
import random

register = template.Library()

@register.filter
def inclusivedictsort(value, arg):
    """
    Sort list of dicts by specified field.

    Put the ones without such field at the end. (generic dictsort removed such from sorted list)
    The main use is to have releases sorted descending by year.

    @param value: a list of dicts
    @param arg: a dict key to sort the list by

    @return: a sorted list of dicts
    """
    decorated = [(i[arg] if arg in i else '', i) for i in value]
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
    Thin wrapper around default slugify to handle extreme unicode cases (such as japanese etc).

    When generic slugify removes all characters in process, we decide to pass
    original value in lowercase with '-' separator in such cases.

    @param value: a string

    @return: a SEO-friendly URL-ish string
    """
    slugified = slugify(value)
    if len(slugified):
        return escape(slugified)
    else:
        return escape(value.strip().replace(' ','-').lower())
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
        return re.sub('((?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z]))', ' ', value)
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
    Append .nyud.net to domain in URL
    """
    url = value.split('/')
    url[2] = url[2]+'.nyud.net'
    return '/'.join(url)
coralize.is_safe = True

