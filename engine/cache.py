from mmda.engine.utils import mmda_logger
from django.conf import settings
from django.core.cache import cache
from couchdbkit.ext.django.loading import get_db
from mmda.artists.templatetags.release_helpers import slugify2


class CachedDocument:
    """
    Template for CachedDocuments.
    """

    # would be nice to  put 'cache_state' here,
    # but couchdbkit architecture makes it tricky atm
    # (place for future improvements)

    def save_any_changes(self):
        """
        Store document in the database if it is marked as 'changes_present'.
        """
        if 'changes_present' in self:
            del self.changes_present
            self.save()
            mmda_logger('db','store',self)

class NginxMemcachedMiddleware:
    """
    Simple middleware that saves response to memcached (for nginx).

    inspired by: http://bretthoerner.com/blog/2008/oct/27/using-nginx-memcached-module-django/
    """
    def process_response(self, request, response):
        if not settings.DEBUG:
            path = request.get_full_path()

            if request.method != "GET" \
            or path.endswith('/feed/') \
            or path.endswith('/refresh/') \
            or response.status_code != 200:
                return response

            # settings.NGINX_CACHE_PREFIX == 'mmda', just like in nginx.conf
            key = "%s:%s" % (settings.NGINX_CACHE_PREFIX, path)
            cache.set(key, response.content)

        return response

def delete_memcached_keys(artist):
    """
    Quick hook that removes artist-related pages from memcached backend.
    """
    if not settings.DEBUG:

        uri_name = slugify2(artist.name)
        uri = (uri_name, artist.get_id)

        # remove all artist pages
        keys = ["/artist/%s/%s/" % uri,
                "/artist/%s/pictures/%s/" % uri,
                "/artist/%s/videos/%s/" % uri,
                "/artist/%s/news/%s/" % uri,
               ]

        # and all artist's releases
        artist_releases = get_db('artists').view('artists/all_artists_releases', key=artist.get_id)
        keys.extend([ "/artist/%s/release/%s/%s/" % (uri_name, slugify2(r['value'][0]), r['value'][1]) for r in artist_releases])

        for key in keys:
            cache.delete("%s:%s" % (settings.NGINX_CACHE_PREFIX, key))
