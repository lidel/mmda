function(doc) {
  for (var url in doc.sources) {
    var items = doc.sources[url].items;
    for (var entry in items) {
      var news = items[entry];
      news['source'] = doc.sources[url].name;
      // date in key takes care of order
      emit( [doc._id, news.date], news);
    }
  }
}
