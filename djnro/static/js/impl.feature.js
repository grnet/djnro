;(function(root, factory) {
    if (typeof define === 'function' && define.amd) {
	define(["jquery"], factory(root));
    }
}(this, function(root){
    'use strict';

    function isBase64Supported() {
	var methods = ['atob', 'btoa'];
	for (var i=0; i < methods.length; i++) {
	    if (!(methods[i] in root) ||
		typeof root[methods[i]] !== 'function') {
		return false;
	    }
	}
	return true;
    }

    function isHistoryAPISupported(){
	var ua = root.navigator.userAgent;
	// We only want Android 2 and 4.0, stock browser, and not Chrome which identifies
	// itself as 'Mobile Safari' as well, nor Windows Phone (issue #1471).
	if ((ua.indexOf('Android 2.') !== -1 ||
	     (ua.indexOf('Android 4.0') !== -1)) &&
	    ua.indexOf('Mobile Safari') !== -1 &&
	    ua.indexOf('Chrome') === -1 &&
	    ua.indexOf('Windows Phone') === -1)
	{
	    return false;
	}
	// Return the regular check
	return !!root.history.pushState;
    }

    function isPlaceholderSupported() {
    	var isOperaMini = Object.prototype.toString.call(window.operamini) === '[object OperaMini]';
    	var isInputSupported = 'placeholder' in document.createElement('input') && !isOperaMini;
    	var isTextareaSupported = 'placeholder' in document.createElement('textarea') && !isOperaMini;
    	return isInputSupported && isTextareaSupported;
    }

    return function($) {
	var fallback = {
	    implementation: function(name) { return name; },
	    isAvailable: true
	}
	return {
	    'jquery.base64': [
		{
		    module: undefined,
		    // module: {
		    //     atob: root.atob,
		    //     btoa: root.btoa
		    // }
		    isAvailable: isBase64Supported()
		},
		fallback
	    ],
	    'history': [
		{
		    module: undefined,
		    // module: root.history,
		    isAvailable: isHistoryAPISupported()
		},
		fallback
	    ],
	    'jquery.placeholder': [
		{
		    module: undefined,
		    isAvailable: isPlaceholderSupported()
		},
		fallback
	    ],
	    'jquery.xdomainrequest': [
		{
		    module: undefined,
		    isAvailable: ($.support.cors || !$.ajaxTransport || !root.XDomainRequest)
		},
		fallback
	    ]
	}
    }
}));
