function(doc) {
if (doc.doc_type == "CachedArtist" && doc.cache_state['mb']) {
    emit(doc.cache_state['mb'][1],{'name':doc.name,'mbid':doc._id});
  }
}

