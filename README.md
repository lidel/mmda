MMDA
====

An old poof-of-concept mashup that used music related APIs, Python and CouchDB to provide various informations about artists.

Developed as a simple demo application for my thesis (in `pl_PL`): [Programowanie i wdrażanie aplikacji sieciowych w języku Python (2010)](http://lidel.org/mmda/) which was a simple introduction to Python-based web development.

Warning: legacy code, no longer maintained
------------

This project *did not aged well* and is left here only due to *personal nostalgia*.   
[MusicBrainz NGS](https://wiki.musicbrainz.org/Next_Generation_Schema) was introduced in 2011, deprecating the old API used by MMDA.    
In the following years the [MusicBrainz.org](http://musicbrainz.org/) site got a lot of neat updates making MMDA functionally obsolete.


Dependencies
------------

    django==1.1.1
    python-memcached==1.45
    python-musicbrainz2==0.7.2
    couchdbkit==0.4.6
    beautifulsoup==3.0.8
    pylast==0.4.26
    surf.sparql_protocol==1.0.0
    python-cjson==1.0.5
    flickrapi==1.4.2
    gdata==2.0.9
    feedparser==4.1
    unidecode==0.04.1
    recaptcha-client==1.0.5
    gunicorn==0.9.1


License
-------

To the extent possible under law, the author have dedicated all copyright and related and neighboring rights to this software to the public domain worldwide. This software is distributed without any warranty. 

You should have received a copy of the CC0 Public Domain Dedication along with this software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>. 

Third party libraries may be available under different license conditions.

