# -*- coding: utf-8
import time
from django.conf import settings

if settings.DEBUG:
    t1 = time.time()
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

