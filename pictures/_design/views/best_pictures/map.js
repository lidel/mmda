function(doc) {
  if (doc.doc_type == "CachedArtistPictures") {
    var i=0;
    if (doc.lastfm) {
        for(var i in doc.lastfm) {
            if (i==5) {
                break;
            } else {
                emit(doc._id,doc.lastfm[i]);
                i++;
            }
        }
    } else if (doc.flickr) {
        for(var i in doc.flickr) {
            if (i==5) {
                break;
            } else {
                emit(doc._id,doc.flickr[i]);
                i++;
            }
        }
    }
  }
}
