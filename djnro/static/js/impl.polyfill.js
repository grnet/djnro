;(function(factory) {
    if (typeof define === 'function' && define.amd) {
	// need a dummy dependency to detect AMD in factory
	define(["module"], factory);
    } else {
	factory();
    }
}(function() {
    'use strict';

    var polyfills = {
	'String.prototype.trim':
	function() {
	    if (!String.prototype.trim) {
		Object.defineProperty(String.prototype, "trim", {
		    value: function() {
			return this.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
		    }
		});
	    }
	},
	'Array.prototype.find':
	function() {
	    if (!Array.prototype.find) {
    		Object.defineProperty(Array.prototype, "find", {
    		    value: function(predicate) {
    			'use strict';
    			if (this == null) {
    			    throw new TypeError('Array.prototype.find called on null or undefined');
    			}
    			if (typeof predicate !== 'function') {
    			    throw new TypeError('predicate must be a function');
    			}
    			var list = Object(this);
    			var length = list.length >>> 0;
    			var thisArg = arguments[1];
    			var value;

    			for (var i = 0; i < length; i++) {
    			    value = list[i];
    			    if (predicate.call(thisArg, value, i, list)) {
    				return value;
    			    }
    			}
    			return undefined;
    		    }
    		});
	    }
	},
	'Array.prototype.forEach':
	function() {
	    if (!Array.prototype.forEach) {
    		Object.defineProperty(Array.prototype, "forEach", {
    		    value: function(callback/*, thisArg*/) {
			var T, k;

			if (this == null) {
			    throw new TypeError('this is null or not defined');
			}

			var O = Object(this);
			var len = O.length >>> 0;

			if (typeof callback !== 'function') {
			    throw new TypeError(callback + ' is not a function');
			}

			if (arguments.length > 1) {
			    T = arguments[1];
			}

			k = 0;

			while (k < len) {
			    var kValue;
			    if (k in O) {
				kValue = O[k];
				callback.call(T, kValue, k, O);
			    }
			    k++;
			}
		    }
		});
	    }
	},
	'Array.prototype.reduce':
	function() {
	    if (!Array.prototype.reduce) {
		Object.defineProperty(Array.prototype, 'reduce', {
		    value: function(callback/*, initialValue*/) {
			if (this === null) {
			    throw new TypeError( 'Array.prototype.reduce ' + 
						 'called on null or undefined' );
			}
			if (typeof callback !== 'function') {
			    throw new TypeError( callback +
						 ' is not a function');
			}

			var o = Object(this);
			var len = o.length >>> 0; 
			var k = 0; 
			var value;

			if (arguments.length == 2) {
			    value = arguments[1];
			} else {
			    while (k < len && !(k in o)) {
				k++;
			    }
			    if (k >= len) {
				throw new TypeError( 'Reduce of empty array ' +
						     'with no initial value' );
			    }
			    value = o[k++];
			}

			while (k < len) {
			    if (k in o) {
				value = callback(value, o[k], k, o);
			    }
			    k++;
			}

			return value;
		    }
		});
	    }
	},
	'Array.prototype.map':
	function() {
	    if (!Array.prototype.map) {
		Object.defineProperty(Array.prototype, 'map', {
		    value: function(callback/*, thisArg*/) {
			var T, A, k;

			if (this == null) {
			    throw new TypeError('this is null or not defined');
			}

			var O = Object(this);
			var len = O.length >>> 0;

			if (typeof callback !== 'function') {
			    throw new TypeError(callback + ' is not a function');
			}

			if (arguments.length > 1) {
			    T = arguments[1];
			}

			A = new Array(len);
			k = 0;

			while (k < len) {
			    var kValue, mappedValue;
			    if (k in O) {
				kValue = O[k];
				mappedValue = callback.call(T, kValue, k, O);

				Object.defineProperty(A, k, {
				    value: mappedValue,
				    writable: true,
				    enumerable: true,
				    configurable: true
				});
				// For best browser support, use the following:
				// A[k] = mappedValue;
			    }
			    k++;
			}

			return A;
		    }
		});
	    }
	},
	'Array.prototype.filter':
	function() {
	    if (!Array.prototype.filter) {
		Object.defineProperty(Array.prototype, 'filter', {
		    value: function(fun/*, thisArg*/) {
			'use strict';

			if (this === void 0 || this === null) {
			    throw new TypeError();
			}

			var t = Object(this);
			var len = t.length >>> 0;
			if (typeof fun !== 'function') {
			    throw new TypeError();
			}

			var res = [];
			var thisArg = arguments.length >= 2 ? arguments[1] : void 0;
			for (var i = 0; i < len; i++) {
			    if (i in t) {
				var val = t[i];
				if (fun.call(thisArg, val, i, t)) {
				    res.push(val);
				}
			    }
			}

			return res;
		    }
		});
	    }
	},
	'Array.isArray':
	function() {
	    if (!Array.isArray) {
		Array.isArray = function(arr) {
		    return Object.prototype.toString.call(arr) === '[object Array]';
		}
	    }
	},
	'Object.keys':
	function() {
	    if (!Object.keys) {
		Object.keys = function(o) {
		    if (o !== Object(o)) {
			throw new TypeError('Object.keys called on a non-object');
		    }
		    var k = [],
			p;
		    for (p in o) {
			if (Object.prototype.hasOwnProperty.call(o,p)) {
			    k.push(p);
			}
		    }
		    return k;
		}
	    }
	},
	'Function.prototype.bind':
	function() {
	    if (!Function.prototype.bind) {
		Object.defineProperty(Function.prototype, 'bind', {
		    value: function(oThis) {
			if (typeof this !== 'function') {
			    // closest thing possible to the ECMAScript 5
			    // internal IsCallable function
			    throw new TypeError('Function.prototype.bind - what is trying to be bound is not callable');
			}

			var aArgs   = Array.prototype.slice.call(arguments, 1),
			    fToBind = this,
			    fNOP    = function() {},
			    fBound  = function() {
				return fToBind.apply(this instanceof fNOP
						     ? this
						     : oThis,
						     aArgs.concat(Array.prototype.slice.call(arguments)));
			    }

			if (this.prototype) {
			    // Function.prototype doesn't have a prototype property
			    fNOP.prototype = this.prototype; 
			}
			fBound.prototype = new fNOP();

			return fBound;
		    }
		});
	    }
	}
    }

    if (arguments.length == 0) {
	for (var k in polyfills) {
	    polyfills[k]();
	}
	return;
    }
    var polyfill = {
	module: function(name) { return polyfills[name]; },
	isAvailable: function(name) {
	    return eval('!' + name) &&
		(name in polyfills);
	}
    }
    var nativeImpl = {
	module: undefined,
	isAvailable: true
    }
    var implementations = {};
    for (var k in polyfills) {
	implementations[k] = [ polyfill, nativeImpl ];
    }
    return implementations;
}));
