$('.gfx li > a[href^=http://www.last.fm]').each(function(){
        $(this).fancybox({
              'padding'             : 0,
              'margin'              : 40,
              'autoScale'           : true,
              'overlayShow'         : false,
              'transitionIn'        : 'elastic',
              'transitionOut'       : 'elastic',
              'easingIn'            : 'easeOutBack',
              'easingOut'           : 'easeOutBack',
              'opacity'             : true,
              'title'               : this.title,
              'titlePosition'       : 'inside',
              'titleFormat'         : function formatTitle(title, currentArray, currentIndex, currentOpts) {
                                      return '<div><div id="fb-caption">' + (title && title.length ? title : '' )  + '</div><div id="fb-nav"><div>'+ (currentIndex + 1) + ' / ' + currentArray.length + '</div><a href="javascript:;" onclick="$.fancybox.prev();"><img alt="prev" src="/static/fancybox/fancy_nav_left.png"/></a><a href="javascript:;" onclick="$.fancybox.next();"><img alt="next" src="/static/fancybox/fancy_nav_right.png"/></a><a id="close-button" href="javascript:;" onclick="$.fancybox.close();"><img alt="close" src="/static/fancybox/fancy_close.png"/></a></div></div>';
                                      },
              'showCloseButton'     : false,
              'showNavArrows'       : false,
              'cyclic'              : true,
              'centerOnScroll'      : true,
              'href'                : $(this).children('img:first-child').attr('alt'),
              'onComplete'          : function() { $('#fb-caption').favicons({insert: 'insertBefore'}); },
              'type'                : 'image'
              });
});
$('.gfx li > a[href^=http://www.flickr.com]').each(function(){
        $(this).fancybox({
              'padding'             : 0,
              'margin'              : 40,
              'autoScale'           : true,
              'overlayShow'         : false,
              'transitionIn'        : 'elastic',
              'transitionOut'       : 'elastic',
              'easingIn'            : 'easeOutBack',
              'easingOut'           : 'easeOutBack',
              'opacity'             : true,
              'title'               : this.title,
              'titlePosition'       : 'inside',
              'titleFormat'         : function formatTitle(title, currentArray, currentIndex, currentOpts) {
                                      return '<div><div id="fb-caption">' + (title && title.length ? title : '' )  + '</div><div id="fb-nav"><div>'+ (currentIndex + 1) + ' / ' + currentArray.length + '</div><a href="javascript:;" onclick="$.fancybox.prev();"><img alt="prev" src="/static/fancybox/fancy_nav_left.png"/></a><a href="javascript:;" onclick="$.fancybox.next();"><img alt="next" src="/static/fancybox/fancy_nav_right.png"/></a><a id="close-button" href="javascript:;" onclick="$.fancybox.close();"><img alt="close" src="/static/fancybox/fancy_close.png"/></a></div></div>';
                                      },
              'showCloseButton'     : false,
              'showNavArrows'       : false,
              'cyclic'              : true,
              'centerOnScroll'      : true,
              'href'                : $(this).children('img:first-child').attr('src').replace(new RegExp("_s", ""), ''),
              'onComplete'          : function() { $('#fb-caption').favicons({insert: 'insertBefore'}); },
              'type'                : 'image'
              });
});
