// copied (simplified) from:
// https://github.com/sindresorhus/query-string
;(function(root, factory) {
    var deps = [
	// polyfills
	'Array.prototype.forEach',
	'Array.prototype.map',
	'Array.prototype.filter',
	'Array.isArray',
	'String.prototype.trim',
	'Object.keys'
    ];
    if (typeof define === 'function' && define.amd) {
	define(deps, factory);
    } else if (typeof module === 'object' && module.exports) {
	var req_deps = (function() {
	    var deps = [];
	    for (var i = 0; i < arguments.length; i++) {
		deps.push(require(dep));
	    }
	    return deps;
	}.apply(null, deps));
	module.exports = factory.apply(root, req_deps);
    } else {
	root.queryString = factory();
    }

}(this, function() {
    'use strict';

    function mergeOpts(aOpts, bOpts) {
	var opts = {};
	if (typeof aOpts !== 'object') {
	    return opts;
	}
	for (var k in aOpts) {
	    if (typeof bOpts === 'object' && k in bOpts) {
		opts[k] = bOpts[k];
	    } else {
		opts[k] = aOpts[k];
	    }
	}
	return opts;
    }

    return {
	opts: {
	    sort: true,
	    multiVal: true
	},
    	parse: function(str, _opts) {
	    var opts = mergeOpts(this.opts, _opts);
    	    var ret = {};
    	    if (typeof str !== 'string') {
    		return ret;
    	    }
    	    str = str
		.trim()
    		.replace(/^(\?|#|&)/, '');
    	    if (!str) {
    		return ret;
    	    }
    	    str.split('&').forEach(function(param) {
    		var parts = param.replace(/\+/g, ' ').split('=');
    		// Firefox (pre 40) decodes `%3D` to `=`
    		// https://github.com/sindresorhus/query-string/pull/37
    		var key = parts.shift();
    		var val = parts.length > 0 ? parts.join('=') : undefined;
    		key = decodeURIComponent(key);
    		// missing `=` should be `null`:
    		// http://w3.org/TR/2012/WD-url-20120524/#collect-url-parameters
    		val = val === undefined ? null : decodeURIComponent(val);
    		if (ret[key] === undefined) {
    		    ret[key] = val;
    		} else if (Array.isArray(ret[key]) && opts.multiVal) {
    		    ret[key].push(val);
    		} else if (opts.multiVal) {
    		    ret[key] = [ret[key], val];
    		}
    	    });
    	    return ret;
    	},
    	stringify: function(obj, _opts) {
	    var opts = mergeOpts(this.opts, _opts);
    	    function aMap(key) {
    		var val = obj[key];
    		if (val === undefined) {
    		    return '';
    		}
    		if (val === null) {
    		    return encodeURIComponent(key);
    		}
    		if (Array.isArray(val)) {
		    if (!opts.multiVal && val.length > 0) {
			return encodeURIComponent(key) + '=' + encodeURIComponent(val[0]);
		    } else {
    			var result = [];
    			val.slice().forEach(function(val2) {
    			    if (val2 === undefined) {
    				return;
    			    }
    			    if (val2 === null) {
    				result.push(encodeURIComponent(key));
    			    } else {
    				result.push(encodeURIComponent(key) + '=' + encodeURIComponent(val2));
    			    }
    			});
    			return result.join('&');
		    }
    		}
    		return encodeURIComponent(key) + '=' + encodeURIComponent(val);
    	    }
    	    function aFilter(x) {
    		return x.length > 0;
    	    }
    	    if (obj) {
    		var okeys = Object.keys(obj);
    		if (opts.sort) {
    		    okeys.sort();
    		}
    		return okeys.map(aMap).filter(aFilter).join('&');
    	    } else {
    		return '';
    	    }
    	}
    }

}));
