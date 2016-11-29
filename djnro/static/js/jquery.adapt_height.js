/**
 * jQuery adapt height
 * @author Zenon Mousmoulas
 */
(function($) {
    $.fn.adapt_height = function(callback) {
	return this.each(function() {
	    var $this = $(this),
	    ah = function($tgt, callback) {
		var realWindowHeight = (typeof(window.innerHeight) == 'number' &&
					$(window).height() < window.innerHeight) ?
		    window.innerHeight :
		    $(window).height(),
		topoffset = $tgt.offset().top;
		if (topoffset + $tgt.height() != realWindowHeight)
		    callback($tgt, realWindowHeight - topoffset);
	    }
	    ah($this, callback);
	    $(window).on('resize orientationchange', function() {
		ah($this, callback);
	    });
	});
    };
})(jQuery);
