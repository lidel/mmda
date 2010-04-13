from django.conf.urls.defaults import *

urlpatterns = patterns('mmda.tags.views',
    url(r'^(?P<tag_id>.+?)/$', 'show_tag', name='show-tag')
)
