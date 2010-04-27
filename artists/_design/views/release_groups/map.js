function(doc) {
if (doc.doc_type == "CachedReleaseGroup" && doc.primary) {
    if (doc.primary[1] == null) {
            emit(doc.artist_mbid,{"title": doc.title, "release_type": doc.release_type, "mbid": doc.primary[0], "year": null});
        } else {
            emit(doc.artist_mbid,{"title": doc.title, "release_type": doc.release_type, "mbid": doc.primary[0], "year": doc.primary[1].substr(0,4), "date":doc.primary[1]});
        }
    }
}

