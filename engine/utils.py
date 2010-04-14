# -*- coding: utf-8
import time
from django.conf import settings

if settings.DEBUG:
    t1 = time.time()
def mmda_logger(entity, action, object_type, object_id=None):
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
        elif action == 'ERROR':
            print "ERROR ->\t(%s)\t%s" % (entity, object_type)
        elif action == 'store':
            print "\t(%s-%s)\t%s         %s:\t %s" % (entity, action, arrows[action], object_type._doc_type, object_type.get_id)
        else:
            print "\t(%s-%s)\t%s         %s:\t\t'%s'" % (entity, action, arrows[action], object_type, object_id)

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

