/*!
 * jQuery hashhandle, v1, 2013-11-28
 * https://github.com/georgekosmidis/jquery-hashhandle
 * 
 * Copyright (c) 2013 George Kosmidis
 * Under GPL license
 * http://www.georgekosmidis.com
 * 
 * GitHub       - https://github.com/georgekosmidis/jquery-hashhandle
 * Source       - https://raw.github.com/georgekosmidis/jquery-hashhandle/master/jquery.hashhandle.js
 * (Minified)   - https://raw.github.com/georgekosmidis/jquery-hashhandle/master/jquery.hashhandle.min.js
 *
 * ****Methods****
 * convertURL: Mapping simulation, from _escaped_fragment_ format to #! format, actually redirects to hide ugly URL
 *             e.g.
 *             <head>...<script>$.fn.HashHandle('convertURL');</script>...</head>
 *             Redirects from http://.../?param1=value1&_escaped_fragment_=k1=v1&k2=v2 to http://.../?param1=value1#!k1=v1&k2=v2
 * hash      : Returns a collection of fragment keys in url fragment
 *             e.g.
 *             For url http://.../?param1=value1#!k1=v1&k2=v2 get p1 with
 *             var k1 =  $.fn.HashHandle("hash").k1;
 * add(k,v)  : Adds key/value to fragment, or changes existing key
 *             e.g.
 *             $.fn.HashHandle("add", "k1", "v1") will change url to 
 *             http://...#!k1=v1
 * add       : Binds an onlick event to the object and adds key/value fragment based on href attribute
 *             e.g.
 *             <a href='#!k2=v2'>...</a>
 *             $("a").HashHandle("add");
 *             Will convert url http://...#!k1=v1 to http://...#!k1=v1&k2=v2
 * remove    : Removes a key
 *             e.g.
 *             $.fn.HashHandle("remove", "k1");
 *             Will convert url http://...#!k1=v1 to http://...
 * clear     : Clears fragment
 *             e.g.
 *             $.fn.HashHandle("clear");
 *             Will convert url http://...#!k1=v1&k2=v2 to http://...
 *
 *
 * ****Example****
 * The following example also user the jquery hash-change plugin found here: http://benalman.com/projects/jquery-hashchange-plugin/
 * 
 *<html>
 * <head>
 *  ...
 *  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js"></script>
 *  <script src="http://github.com/cowboy/jquery-hashchange/raw/master/jquery.ba-hashchange.min.js"></script>
 *  <script src="https://github.com/georgekosmidis/hash-handle/raw/master/...."></script>
 *  <script>$.fn.HashHandle('convertURL');</script>
 *  <script>$(document).ready(function () { 
 *           $(".HashHandle").HashHandle('add');
 *          });
 *  </script>
 *    ...
 *  </head>
 *  <body> 
 *   ...
 *   <a href='#!filter=somefitler' class='HashHandle'>Change filtering</a>
 *   <a href='#!sort=somesorting' class='HashHandle'>Change sorting</a>
 *   <a href='#!'>Reset</a>
 *   <div id='table-that-needs-filtering-and-sorting'>...</div>
 *   ...
 *   <script>
 *    //hash change event
 *    $(window).hashchange(function (e) {
 *     var filter = $.fn.HashHandle("hash").filter;
 *     var sort = $.fn.HashHandle("hash").sort;
 *     if(filter != undefined || sort != undefined){
 *      $.get("/GET_DATA_FOR_DIV?filter=" + filter + "&sort="+sort, function (data) {
 *       $("#table-that-needs-filtering-and-sorting").html(data);
 *      });
 *     }
 *    });
 *    //trigger hash change on load
 *    $(window).hashchange();
 *   </script>
 *   ...
 *  </body>
 *</html>
 */


(function ($) {

    var methods = {
        //get params from location
        convertURL: function () {
            //https://developers.google.com/webmasters/ajax-crawling/docs/specification
            //Mapping from _escaped_fragment_ format to #! format
            var l = window.location.toString();

            if (l.indexOf("_escaped_fragment_=") > -1) {
                var a = l.split("_escaped_fragment_=");
                if (a[0].lastIndexOf("&") == a[0].length - 1)
                    a[0] = a[0].substr(0, a[0].length - 1);
                if (a[0].lastIndexOf("?") == a[0].length - 1)
                    a[0] = a[0].substr(0, a[0].length - 1);

                window.location = a[0] + "#!" + decodeURIComponent( a[1] );
            }

        },
        hash: function () {
            var a = methods["_fragment"].call(this, null);
            return a;
        },
        //add a new key=value hash or change an old one
        add: function (k, v) {
            //if add called without params, bind click 
            if (k == undefined) {
                return $(this).bind('click.HashHandle', function (event) { methods["_addHref"].call(this, event, $(this)); });
            }
            var a = methods["_fragment"].call(this, null);
            a[k] = v;
            return methods[arguments.length > 1 &&
			   arguments[arguments.length - 1] === true ?
			   "_goHard" :
			   "_go"].call(this, a);
        },
	addHard: function (k, v) {
	    var args = Array.prototype.slice.call(arguments);
	    args.push(true);
            return methods["add"].apply(this, args);
	},
        //clear hashes
        clear: function () {
            a = {};
            return methods["_go"].call(this, a);
        },
        //remove a hash entry by key
        remove: function (k) {
            var a = methods["_fragment"].call(this, null);
            delete a[k];
            return methods[arguments.length > 1 &&
			   arguments[1] === true ?
			   "_goHard" :
			   "_go"].call(this, a);
        },
        removeHard: function (k) {
            return methods["remove"].call(this, k, true);
	},
        //add an href loc to hash
        _addHref: function (event, o) {
            event.preventDefault();
            var href = o.attr("href");
            if (href != "") {
                var a = methods["_fragment"].call(this, null);
                $.extend(a, methods["_fragment"].call(this, href));
                return methods["_go"].call(this, a);
            }
            return this;
        },
        //get fragment (everything after first #!)
        _fragment: function (urlarg) {
            var url = urlarg || location.href;
            var urlparts = url.match(/^([^#]*)#?(.*)$/);
	    // if hash not empty
	    if (urlparts[2]) {
		//if hashbang = #!, chop first char of hash
		if (urlparts[2].search('!') == 0) {
		    urlparts[2] = urlparts[2].substr(1);
		//if hashbang != #! and urlarg not specified, update property
		} else if (urlarg != url) {
		    methods["_hashbang"].call(this, '#');
		}
	    }
            // var af = url.split(/#!?/);
            // var f = (af.length > 1) ? af[af.length - 1] : "";
	    var f = urlparts[2];
            var a = {};
            if (f != "") {
                var ap = f.split("&"),
		    apiarr = [];
                for (var i=0; i < ap.length; i++) {
		    apiarr = ap[i].split(/[=]/);
		    if (apiarr.length < 2) {
			apiarr = ap[i].split(/[-]/);
		    }
                    a[apiarr[0]] = apiarr[1];
		}
            }
            return a;
        },
        //join collection
        _join: function (cl) {
            var a = [];
            for (var k in cl)
                a.push(k + '=' + (cl[k] || ''));
            return a.join('&');
        },
        //actually add hash to url
        _go: function (a) {
            var f = methods["_join"].call(this, a);
	    $.changeFragment((f == "") ? f : methods["_hashbang"].call(this) + f,
			     arguments.length > 1 ?
			     arguments[1] :
			     undefined);
            return this;
        },
        _goHard: function (a) {
            return methods["_go"].call(this, a, 'replace');
        },
        //instance
        _ctor: function () {
            return this;
        },
	//modify the hashbang used for actually adding the hash to url
	_hashbang: function (hashbang) {
	    if (hashbang) {
		properties['hashbang'] = hashbang;
	    }
	    return properties['hashbang'];
	}
    };
    var properties = {
	hashbang: '#!'
    };

    $.fn.HashHandle = function (method) {

        if (!methods[method])
            throw "Invalid method '" + method + "'";

        if (methods[method])
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));

        //else if ( typeof method === "object" || !method ) 
        //	return methods._ctor.apply( this, arguments );

        return this;
    };

    $.changeFragment = function(hash, act, state, trhsevt) {
	// force string
	hash = hash ? String(hash) : '';

	if (act == "replace")
	    act = "replaceState";
	else
	    act = "pushState";

	if (typeof state != "object")
	    state = {};

	// force boolean
	trhsevt = Boolean(typeof trhsevt == "undefined" ? true : trhsevt);

	if (hash.length != 0 && hash.indexOf('#') == -1)
	    hash = '#' + hash;
	else if (hash.indexOf('#') > 0)
	    return false;

	var scrollV, scrollH, loc = window.location;

	if (loc.hash == hash)
	    return true;

	if (act in history) {
	    // console.log('act '+ act +' in history');
            history[act](state, "", loc.pathname + loc.search + hash);
	    if (trhsevt)
		$(window).trigger('popstate');
	} else {
	    // console.log('act '+ act +' NOT in history');
            // Prevent scrolling by storing the page's current scroll offset
            scrollV = document.body.scrollTop;
            scrollH = document.body.scrollLeft;

            loc.hash = hash;

            // Restore the scroll offset, should be flicker free
            document.body.scrollTop = scrollV;
            document.body.scrollLeft = scrollH;
	}
	return true;
    }

})(jQuery);
