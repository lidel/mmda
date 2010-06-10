function(doc) {
  if (doc.doc_type == "CachedReleaseGroup" && doc.releases) {
    for (var mbid in doc.releases) {
      emit(doc.artist_mbid, [doc.releases[mbid]['title'], mbid]);
    }
  }
}

