function(doc) {
  if (doc.doc_type == "CachedArtistPictures" && doc.lastfm) {
    var i=0;
    for(var i in doc.lastfm) {
      if (i==5) {
        break;
      } else {
        emit(doc._id,doc.lastfm[i]);
        i++;
      }
    }
  }
}
