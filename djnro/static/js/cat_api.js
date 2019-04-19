;(function(root, factory) {
    var deps = ['jquery', 'querystring',
		// polyfills
		'Array.prototype.find', 'Array.prototype.reduce',
		'Array.prototype.forEach', 'String.prototype.trim',
		'Array.isArray', 'Object.keys'];
    if (typeof define === 'function' && define.amd) {
	define(deps, function() {
	    // return (root.ConfigurationAssistantTool = factory.apply(root, arguments));
	    return factory.apply(root, arguments);
	});
    } else if (typeof module === 'object' && module.exports) {
	// var req_deps = deps.map(function(dep) {
	//     return require(dep);
	// });
	var req_deps = (function() {
	    var deps = [];
	    for (var i = 0; i < arguments.length; i++) {
		deps.push(require(dep));
	    }
	    return deps;
	}.apply(null, deps));
	// module.exports = (root.ConfigurationAssistantTool = factory.apply(root, req_deps));
	module.exports = factory.apply(root, req_deps);
    } else {
	root.ConfigurationAssistantTool = factory.call(root, root.jQuery);
    }

}(this, function($, queryString) {
    'use strict';

    var root = this;

    // Arguments -> Array converter that (supposedly) does not kill optimizations
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/arguments
    // However this still means passing the Arguments object around...
    if (!Array.from_arguments) {
	Array.from_arguments = function() {
	    return (arguments.length === 1 ?
		    [arguments[0]] :
		    Array.apply(null, arguments));
	}
    }
    // The equivalent for (non-working):
    // new Obj.apply(null, constructor_args_array)
    // another alternative (which requires .bind):
    // new (Function.prototype.bind.apply(Obj, [null].concat(args)));
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/apply
    if (!Function.prototype.new_with_array) {
    	Object.defineProperty(Function.prototype, "new_with_array", {
    	    value: function(aArgs) {
    // Function.prototype.new_with_array = function(aArgs) {
		var fConstructor = this,
		    fNewConstr = function() {
			fConstructor.apply(this, aArgs);
		    };
		fNewConstr.prototype = fConstructor.prototype;
		return new fNewConstr();
    // }
	    }
	});
    }

    // Inheritance: We'll fall back to this instead of a polyfill!
    // but we don't use inheritance...
    // function createObject(proto) {
    // 	function ctor() { }
    // 	ctor.prototype = proto;
    // 	return new ctor();
    // }
    function flipObject(orig) {
	var key, flip = {};
	for (key in orig) {
            if (orig.hasOwnProperty(key)) {
		flip[orig[key]] = key;
            }
	}
	return flip;
    }

    var getQueryParameters,
	getQueryString;
    (function() {
	var qs = queryString || root.queryString,
	    opts = {
		sort: true,
		multiVal: false
	    };
	getQueryParameters = function(str) {
	    return qs.parse(str, opts);
	}
	getQueryString = function(obj) {
	    return qs.stringify(obj, opts);
	}
    }());


    var CAT, CatIdentityProvider, CatProfile, CatDevice;
    
    // ***** CAT API *****
    var API_TRANSLATIONS = {
	2: {
	    listLanguages:
	    {
		to: {},
		from:
		{
		    id: 'lang'
		}
	    },
	    listCountries:
	    {
		to: {},
		from:
		{
		    id: 'federation'
		}
	    },
	    listIdentityProviders:
	    {
		to:
		{
		    id: 'federation'
		},
		from:
		{
		    id: 'idp'
		}
	    },
	    listAllIdentityProviders:
	    {
		to: {},
		from:
		{
		    id: 'idp'
		}
	    },
	    orderIdentityProviders:
	    {
		to:
		{
		    id: 'federation'
		},
		from:
		{
		    id: 'idp'
		}
	    },
	    listProfiles:
	    {
		to:
		{
		    id: 'idp'
		},
		from:
		{
		    id: 'profile'
		}
	    },
	    listDevices:
	    {
		to:
		{
		    id: 'profile'
		},
		from:
		{
		    id: 'device'
		}
	    },
	    generateInstaller:
	    {
		to:
		{
		    id: 'device'
		},
		from: {}
	    },
	    downloadInstaller:
	    {
		to:
		{
		    id: 'device'
		},
		from: {}
	    },
	    profileAttributes:
	    {
		to:
		{
		    id: 'profile'
		},
		// nested devices obj
		from:
		{
		    id: 'device'
		}
	    },
	    sendLogo:
	    {
		to:
		{
		    id: 'idp'
		},
		from: {}
	    },
	    deviceInfo:
	    {
		to:
		{
		    id: 'device'
		},
		from: {}
	    },
	    detectOS:
	    {
		to: {},
		from:
		{
		    id: 'device'
		}
	    }
	}
    }
    CAT = function(options) {
	var cat_eduroam_org_api = 'https://cat.eduroam.org/user/API.php',
	    cat_eduroam_org_ldlbase = cat_eduroam_org_api.replace('user/API.php', '');
	this._defaults = {
	    apiBase: cat_eduroam_org_api,
	    apiBaseD: cat_eduroam_org_api,
	    localDownloadBase: cat_eduroam_org_ldlbase,
	    touCallBack: undefined,
	    lang: 'en',
	    redirectDownload: true,
	    redirectLocateUser: true,
	    api_version: 1
	}
        this.options = $.extend({}, this._defaults, options);
	this._cache = {};
	this._xhrcache = {};
    }
    CAT.prototype.API_TRANSLATIONS = API_TRANSLATIONS;
    CAT.prototype.apiBase = function(direct, newApiBase) {
	if (typeof newApiBase !== 'undefined') {
	    if (direct === true) {
		this.options.apiBaseD = newApiBase;
	    } else {
		this.options.apiBase = newApiBase;
	    }
	}
    	return direct === true ?
	    this.options.apiBaseD : this.options.apiBase;
    }
    CAT.prototype.localDownloadBase = function(newLDlBase) {
	if (typeof newLDlBase !== 'undefined') {
	    this.options.localDownloadBase = newLDlBase;
	}
	return this.options.localDownloadBase;
    }
    CAT.prototype.touCallBack = function(newTouCallBack) {
	if (typeof newTouCallBack !== 'undefined') {
	    this.options.touCallBack = newTouCallBack;
	}
	return this.options.touCallBack;
    }
    CAT.prototype.lang = function(newLang) {
	if (typeof newLang !== 'undefined') {
	    this.options.lang = newLang;
	}
	return this.options.lang;
    }
    CAT.prototype.downloadRedirect = function(newRedirectDownload) {
	if (typeof newRedirectDownload !== 'undefined') {
	    this.options.redirectDownload = newRedirectDownload;
	}
	return this.options.redirectDownload;
    }
    CAT.prototype.apiVersionGetTranslations = function(act, direction, reverse) {
	var param_translations = this.API_TRANSLATIONS,
	    api_version = this.options.api_version;
	if ((api_version in param_translations) &&
	    !!act && (act in param_translations[api_version]) &&
	    !!direction && (direction in param_translations[api_version][act])) {
	    return reverse ?
		flipObject(param_translations[api_version][act][direction]) :
		param_translations[api_version][act][direction];
	} else {
	    return {};
	}
    }
    CAT.prototype.apiVersionGetTranslated = function(obj, act, direction, reverse) {
	var args = Array.prototype.slice.call(arguments, 1),
	    translations = this.apiVersionGetTranslations.apply(this, args),
	    obj_keys = Object.keys(obj),
	    obj_translated;
	if (Array.isArray(obj)) {
	    obj_translated = [];
	} else {
	    obj_translated = {};
	}
	for (var key in obj_keys) {
	    key = obj_keys[key];
	    // skip hasOwnProperty check on Arrays?
	    if (!Array.isArray(obj) &&
		!obj.hasOwnProperty(key)) {
		continue;
	    }
	    if (obj[key] instanceof Object) {
		obj_translated[key] = this.apiVersionGetTranslated
		    .apply(this, [obj[key]].concat(args));
	    } else {
		obj_translated[key] = obj[key];
	    }
	    if (!Array.isArray(obj) &&
		(key in translations)) {
		obj_translated[translations[key]] = obj_translated[key];
		delete obj_translated[key];
	    }
	}
	return obj_translated;
    }
    CAT.prototype._qryRespTranslate = function(data, jqxhr) {
	if (this.options.api_version !== 1 &&
	    !!jqxhr._cat_qro && !!jqxhr._cat_qro.action) {
	    return this.apiVersionGetTranslated(data,
						jqxhr._cat_qro.action,
						'from',
						true);
	}
	return data;
    }
    CAT.prototype.query = function(qro) {
	if (!('action' in qro)) {
	    // throw something?
	    return null;
	}
	if (!('lang' in qro)) {
	    qro.lang = this.lang();
	}

	if (this.options.api_version !== 1) {
	    qro.api_version = this.options.api_version;
	    qro = this.apiVersionGetTranslated(qro, qro.action, 'to');
	}
	var dtype = 'json';
	var ep = ((qro.action.search(/downloadInstaller/) == 0 &&
		   this.options.redirectDownload === true) ||
		  (qro.action == 'locateUser' &&
		   this.options.redirectLocateUser === true)) ?
	    this.options.apiBaseD : this.options.apiBase;
	var directUri = [ep, getQueryString(qro)].join('?');

	switch (qro.action) {
	case 'downloadInstallerUri':
	    qro.action = qro.action.replace(/Uri$/, '');
	    directUri = [ep, getQueryString(qro)].join('?');
	    return $.when().then(function(){
		return directUri;
	    });
	    break;
	case 'downloadInstaller':
	    root.location.href = directUri;
	    return $.when().then(function(){
		return directUri;
	    });
	    break;
	case 'sendLogoUri':
	    qro.action = qro.action.replace(/Uri$/, '');
	    directUri = [ep, getQueryString(qro)].join('?');
	    return $.when().then(function(){
		return directUri;
	    });
	    break;
	case 'sendLogo':
	    // delete dtype;
	    return $.when().then(function(){
		return $('<img>').attr('src', directUri);
	    });
	    break;
	case 'deviceInfo':
	    dtype = 'html';
	    // fallthrough
	default:
	    if (directUri in this._xhrcache) {
		return this._xhrcache[directUri];
	    } else {
		this._xhrcache[directUri] = $.ajax({
		    dataType: dtype,
		    url: ep,
		    data: qro,
		    beforeSend: function(jqxhr) {
			jqxhr._cat_ep = ep;
			jqxhr._cat_qro = qro;
		    }
		});
		return this._xhrcache[directUri];
	    }
	}
    }
    CAT.prototype._qry0args = function(act) {
	if (!act) {
	    // throw something?
	    return null;
	}
	var $cat = this;
	if (act in this._cache) {
	    // return a (resolved) promise for consistency
	    return $.when().then(function(){
		return $cat._cache[act];
	    });
	}
	var qro = {
	    action: act,
	    lang: undefined
	}
	var cb = function(ret) {
	    if (!!arguments[1] &&
		arguments[1] != 'success') {
		return null;
	    }
	    if (!!!this.dataType ||
		this.dataType != 'json') {
		return null;
	    }
	    if (ret.status === 'ok') {
		ret.status = 1;
		if (!('data' in ret)) {
		    ret.data = {};
		    for (var k in ret) {
			if (k != 'status' && k != 'data' &&
			    ret.hasOwnProperty(k)) {
			    ret.data[k] = ret[k];
			}
		    }
		}
	    }
	    if (!('status' in ret) || ret.status != 1 || !('data' in ret)) {
		return $cat._cache[act] = null;
	    }
	    if (!!ret.tou) {
		if (!('_tou' in $cat) || $cat._tou != ret.tou) {
		    $cat._tou = ret.tou;
		    if (typeof $cat.options.touCallBack === 'function') {
			$cat.options.touCallBack(ret.tou);
		    }
		}
	    }
	    var jqxhr = !!arguments[2] ? arguments[2] : {};
	    return $cat._cache[act] = $cat._qryRespTranslate(ret.data, jqxhr);
	}
	return this.query(qro)
	    .then(cb, cb);
    }
    CAT.prototype._qry1args = function(act, lang) {
	if (!act) {
	    // throw something?
	    return null;
	}
	if (typeof lang === 'undefined') {
	    lang = this.lang();
	}
	var $cat = this;
	if ((act in this._cache) &&
	    (lang in this._cache[act])) {
	    // return a (resolved) promise for consistency
	    return $.when().then(function(){
		return $cat._cache[act][lang];
	    });
	}
	var qro = {
	    action: act
	}
	if (lang !== this.lang()) {
	    qro.lang = lang;
	}
	var cb = function(ret) {
	    if (!!arguments[1] &&
		arguments[1] != 'success') {
		return null;
	    }
	    if (!(act in $cat._cache)) {
		$cat._cache[act] = {};
	    }
	    // if (typeof ret === 'string' ||
	    // 	ret instanceof $) {
	    // 	return $cat._cache[act][lang] = ret;
	    // }
	    if (!!!this.dataType ||
		this.dataType != 'json') {
		return null;
	    }
	    var jqxhr = !!arguments[2] ? arguments[2] : {};
	    // listAllIdentityProviders returns just an array
	    if (Array.isArray(ret)) {
		return $cat._cache[act][lang] =
		    $cat._qryRespTranslate(ret, jqxhr);
	    }
	    if (ret.status === 'ok') {
		ret.status = 1;
		if (!('data' in ret)) {
		    ret.data = {};
		    for (var k in ret) {
			if (k != 'status' && k != 'data' &&
			    ret.hasOwnProperty(k)) {
			    ret.data[k] = ret[k];
			}
		    }
		}
	    }
	    if (!('status' in ret) || ret.status != 1 || !('data' in ret)) {
		return $cat._cache[act][lang] = null;
	    }
	    if (!!ret.tou) {
		if (!('_tou' in $cat) || $cat._tou != ret.tou) {
		    $cat._tou = ret.tou;
		    if (typeof $cat.options.touCallBack === 'function') {
			$cat.options.touCallBack(ret.tou);
		    }
		}
	    }
	    return $cat._cache[act][lang] =
		$cat._qryRespTranslate(ret.data, jqxhr);
	}
	return this.query(qro)
	    .then(cb, cb);
    }
    CAT.prototype._qry2args = function(act, idname, idval, lang) {
	if (!act ||
	    !idname ||
	    (typeof !idval === 'undefined')) {
	    // throw something?
	    return null;
	}
	if (typeof lang === 'undefined') {
	    lang = this.lang();
	}
	var $cat = this;
	if ((act in this._cache) &&
	    (idval in this._cache[act]) &&
	    (lang in this._cache[act][idval])) {
	    // return a (resolved) promise for consistency
	    return $.when().then(function() {
		return $cat._cache[act][idval][lang];
	    });
	}
	var qro = {
	    action: act
	}
	if (lang !== this.lang()) {
	    qro.lang = lang;
	}
	qro[idname] = idval;
	var cb = function(ret) {
	    if (!!arguments[1] &&
		arguments[1] != 'success') {
		return null;
	    }
	    if (!(act in $cat._cache)) {
		$cat._cache[act] = {};
	    }
	    if (!(idval in $cat._cache[act])) {
		$cat._cache[act][idval] = {};
	    }
	    if (typeof ret === 'string' ||
		ret instanceof $) {
		return $cat._cache[act][idval][lang] = ret;
	    }
	    if (!!!this.dataType ||
		this.dataType != 'json') {
		return null;
	    }
	    if (ret.status === 'ok') {
		ret.status = 1;
		if (!('data' in ret)) {
		    ret.data = {};
		    for (var k in ret) {
			if (k != 'status' && k != 'data' &&
			    ret.hasOwnProperty(k)) {
			    ret.data[k] = ret[k];
			}
		    }
		}
	    }
	    if (!('status' in ret) || ret.status != 1 || !('data' in ret)) {
		return $cat._cache[act][idval][lang] = null;
	    }
	    if (!!ret.tou) {
		if (!('_tou' in $cat) || $cat._tou != ret.tou) {
		    $cat._tou = ret.tou;
		    if (typeof $cat.options.touCallBack === 'function') {
			$cat.options.touCallBack(ret.tou);
		    }
		}
	    }
	    var jqxhr = !!arguments[2] ? arguments[2] : {};
	    return $cat._cache[act][idval][lang] =
		$cat._qryRespTranslate(ret.data, jqxhr);
	}
	return this.query(qro)
	    .then(cb, cb);
    }
    CAT.prototype._qry3args = function(act, id1name, id1val, id2name, id2val, lang) {
	if (!act ||
	    !id1name ||
	    (typeof !id1val === 'undefined') ||
	    !id2name ||
	    (typeof id2val === 'undefined')) {
	    // throw something?
	    return null;
	}
	if (typeof lang === 'undefined') {
	    lang = this.lang();
	}
	var $cat = this;
	if ((act in this._cache) &&
	    (id1val in this._cache[act]) &&
	    (id2val in this._cache[act][id1val]) &&
	    (lang in this._cache[act][id1val][id2val])) {
	    // return a (resolved) promise for consistency
	    return $.when().then(function() {
		return $cat._cache[act][id1val][id2val][lang];
	    });
	}
	var qro = {
	    action: act
	}
	if (lang !== this.lang()) {
	    qro.lang = lang;
	}
	qro[id1name] = id1val;
	qro[id2name] = id2val;
	var cb = function(ret) {
	    if (!!arguments[1] &&
		arguments[1] != 'success') {
		return null;
	    }
	    if (!(act in $cat._cache)) {
		$cat._cache[act] = {};
	    }
	    if (!(id1val in $cat._cache[act])) {
		$cat._cache[act][id1val] = {};
	    }
	    if (!(id2val in $cat._cache[act][id1val])) {
		$cat._cache[act][id1val][id2val] = {};
	    }
	    if (typeof ret === 'string' ||
		ret instanceof $) {
		return $cat._cache[act][id1val][id2val][lang] = ret;
	    }
	    if (!!!this.dataType ||
		this.dataType != 'json') {
		return null;
	    }
	    if (ret.status === 'ok') {
		ret.status = 1;
		if (!('data' in ret)) {
		    ret.data = {};
		    for (var k in ret) {
			if (k != 'status' && k != 'data' &&
			    ret.hasOwnProperty(k)) {
			    ret.data[k] = ret[k];
			}
		    }
		}
	    }
	    if (!('status' in ret) || ret.status != 1 || !('data' in ret)) {
		return $cat._cache[act][id1val][id2val][lang] = null;
	    }
	    if (!!ret.tou) {
		if (!('_tou' in $cat) || $cat._tou != ret.tou) {
		    $cat._tou = ret.tou;
		    if (typeof $cat.options.touCallBack === 'function') {
			$cat.options.touCallBack(ret.tou);
		    }
		}
	    }
	    var jqxhr = !!arguments[2] ? arguments[2] : {};
	    return $cat._cache[act][id1val][id2val][lang] =
		$cat._qryRespTranslate(ret.data, jqxhr);
	}
	return this.query(qro)
	    .then(cb, cb);
    }

    CAT.prototype.listLanguages = function() {
	return this._qry0args('listLanguages');
    }
    CAT.prototype.listLanguagesByID = function() {
	return this._getEntitiesByID('listLanguages');
    }
    CAT.prototype.getLanguageDisplay = function(lang) {
	if (typeof lang === 'undefined') {
	    lang = this.lang();
	}
	var cb = function(languages_by_id) {
	    if (!!languages_by_id &&
		(lang in languages_by_id) &&
		('display' in languages_by_id[lang])) {
		return languages_by_id[lang].display;
	    } else {
		return null;
	    }
	}
	return $.when(
	    this.listLanguagesByID()
	).then(cb, cb);
    }
    CAT.prototype._getEntitiesByID = function() {
	var args = Array.prototype.slice.call(arguments),
	    act = args.shift(),
	    _act = act + 'ByID',
	    countryid;
	var langIdx = 0;
	switch (act) {
	case 'listLanguages':
	    break;
	case 'listAllIdentityProviders':
	    break;
	case 'listIdentityProviders':
	    countryid = args[0];
	    langIdx += 1;
	    break;
	default:
	    // throw something?
	    return null;
	}
	var lang = (langIdx in args) ? args[langIdx] : undefined;
	if (typeof lang === 'undefined') {
	    lang = this.lang();
	}
	var $cat = this;
	var d = new $.Deferred();
	if ((_act in this._cache) &&
	    (lang in this._cache[_act])) {
	    // use a (resolved) promise for consistency
	    d.resolve(this._cache[_act][lang]);
	} else {
	    var cb = function(ret) {
		if (Array.isArray(ret)) {
		    if (!(_act in $cat._cache)) {
			$cat._cache[_act] = {};
		    }
		    switch (act) {
		    case 'listLanguages':
			// no lang parameter for listLanguages, but
			// we need to use it for _cache lookups
			if (!(lang in $cat._cache[_act])) {
			    $cat._cache[_act][lang] = {};
			}
			for (var idx = 0; idx < ret.length; idx++) {
			    if ('id' in ret[idx]) {
				$cat._cache[_act][lang][ret[idx].id] = ret[idx];
			    }
			}
			d.resolve($cat._cache[_act][lang]);
			break;
		    case 'listAllIdentityProviders':
			if (!(lang in $cat._cache[_act])) {
			    $cat._cache[_act][lang] = {};
			}
			for (var idx = 0; idx < ret.length; idx++) {
			    if ('entityID' in ret[idx]) {
				$cat._cache[_act][lang][ret[idx].entityID] = ret[idx];
			    }
			}
			d.resolve($cat._cache[_act][lang]);
			break;
		    case 'listIdentityProviders':
			if (typeof countryid === 'undefined') {
			    d.fail(null) // not sure!
			    break;
			}
			if (!(countryid in $cat._cache[_act])) {
			    $cat._cache[_act][countryid] = {};
			}
			if (!(lang in $cat._cache[_act][countryid])) {
			    $cat._cache[_act][countryid][lang] = {};
			}
			for (var idx = 0; idx < ret.length; idx++) {
			    if ('id' in ret[idx]) {
				$cat._cache[_act][countryid][lang][ret[idx].id] = ret[idx];
			    }
			}
			d.resolve($cat._cache[_act][countryid][lang]);
			break;
		    }
		} else {
		    d.fail(null); // not sure!
		}
	    }
	    this[act].apply(this, args)
		.then(cb, cb);
	}
	return d.promise();
    }
    CAT.prototype.listAllIdentityProviders = function(lang) {
	return this._qry1args('listAllIdentityProviders', lang);
    }
    CAT.prototype.listAllIdentityProvidersByID = function(lang) {
	var args = Array.prototype.slice.call(arguments);
	args.unshift('listAllIdentityProviders');
	return this._getEntitiesByID.apply(this, args);
    }
    CAT.prototype.listIdentityProviders = function(countryid, lang) {
	return this._qry2args('listIdentityProviders', 'id', countryid, lang);
    }
    CAT.prototype.listIdentityProvidersByID = function(countryid, lang) {
	var args = Array.prototype.slice.call(arguments);
	args.unshift('listIdentityProviders');
	return this._getEntitiesByID.apply(this, args);
    }
    CAT.prototype.listProfiles = function(idpid, lang, sort) {
	sort = sort ? 1 : 0;
	return this._qry3args('listProfiles', 'id', idpid, 'sort', sort, lang);
    }
    CAT.prototype.profileAttributes = function(profid, lang) {
	return this._qry2args('profileAttributes', 'id', profid, lang);
    }
    CAT.prototype.listDevices = function(profid, lang) {
	return this._qry2args('listDevices', 'id', profid, lang);
    }
    CAT.prototype.generateInstaller = function(profid, osid, lang) {
	return this._qry3args('generateInstaller', 'profile', profid, 'id', osid, lang);
    }
    CAT.prototype.downloadInstaller = function(profid, osid, lang, dryrun) {
	var $cat = this;
	var cb = function(ret) {
	    if (!!ret && ('link' in ret)) {
		var qs = ret.link.replace(/^.*\?/, ''),
		    qro = getQueryParameters(qs);
		if (dryrun) {
		    qro.action += 'Uri';
		}
		return $cat.query(qro);
	    } else {
		return ret;
	    }
	}
	return $.when(
	    this.generateInstaller.apply(this, arguments)
	).then(cb, cb);
    }
    CAT.prototype.deviceInfo = function(profid, osid, lang) {
	return this._qry3args('deviceInfo', 'profile', profid, 'id', osid, lang);
    }
    CAT.prototype.sendLogo = function(idpid, lang, dryrun) {
	var act = 'sendLogo';
	if (!!dryrun) {
	    act += 'Uri';
	}
	return this._qry2args(act, 'id', idpid, lang);
    }
    CAT.prototype.locateUser = function() {
	return this._qry0args('locateUser');
    }
    CAT.prototype.detectOS = function() {
	return this._qry0args('detectOS');
    }
    CAT.prototype.orderIdentityProviders = function(countryid, geo, lang) {
	var geo_encoded;
	if (typeof geo === 'object' &&
	    ('lat' in geo) && parseFloat(geo.lat) &&
	    ('lon' in geo) && parseFloat(geo.lon)) {
	    geo_encoded = geo.lat + ':' + geo.lon;
	}
	return typeof geo_encoded !== 'undefined' ?
	    this._qry3args('orderIdentityProviders',
			   'id', countryid,
			   'location', geo_encoded,
			   lang) :
	    this._qry2args('orderIdentityProviders',
			   'id', countryid,
			   lang);
    }

    // ***** CAT Identity Provider *****
    CatIdentityProvider = function(cat, id, lang) {
	this.cat = cat;
	this.id = id;
	this.lang = lang;
    }
    CatIdentityProvider.prototype.getRaw = function() {
	var $idp = this;
	var cb = function (ret) {
	    if (!!ret && ($idp.id in ret)) {
		return ret[$idp.id];
	    } else {
		return null;
	    }
	}
	return $.when(
	    this.cat.listAllIdentityProvidersByID(this.lang)
	).then(cb, cb);
    }
    CatIdentityProvider.prototype._getProp = function(rawFunc, prop) {
	var cb = function(ret) {
	    if (typeof prop === 'undefined') {
		return null;
	    }
	    if (!!ret &&
		(prop in ret)) {
		return ret[prop];
	    } else {
		return null;
	    }
	}
	return $.when(
	    rawFunc.call(this)
	).then(cb, cb);
    }
    CatIdentityProvider.prototype.getEntityID = function() {
	return this._getProp(this.getRaw, 'entityID');
    }
    CatIdentityProvider.prototype.getCountry = function() {
	return this._getProp(this.getRaw, 'country');
    }
    CatIdentityProvider.prototype.getIconID = function() {
	return this._getProp(this.getRaw, 'icon');
    }
    CatIdentityProvider.prototype.getIconURL = function() {
	var returnUrlOnly = true;
	return this.getIcon(returnUrlOnly);
    }
    CatIdentityProvider.prototype.getIcon = function(returnUrl) {
	var $idp = this,
	    returnUrl = !!returnUrl;
	var cb = function(ret) {
	    if (ret != null &&
		parseInt(ret)) {
		return $idp.cat.sendLogo(ret, this.lang, returnUrl);
	    }
	    return ret;
	}
	return $.when(
	    this._getProp(this.getRaw, 'icon')
	).then(cb, cb);
    }
    CatIdentityProvider.prototype.getTitle = function() {
	return this._getProp(this.getRaw, 'title');
    }
    CatIdentityProvider.prototype.getDisplay = function() {
	return this._getProp(this.getRaw, 'title');
    }
    CatIdentityProvider.prototype.getGeo = function() {
	var cb = function(ret) {
	    if (Array.isArray(ret)) {
		var geo = [];
		ret.forEach(function(cur, idx) {
		    var coord = {
			lat: parseFloat(cur.lat),
			lon: parseFloat(cur.lon)
		    }
		    // necessary hack because CAT apparently may return duplicate coords!
		    if (geo.find(function(cur) {
			return (JSON.stringify(cur) === JSON.stringify(coord));
		    }) === undefined) {
			geo.push(coord);
		    }
		});
		return geo;
	    } else {
		return null;
	    }
	}
	return $.when(
	    this._getProp(this.getRaw, 'geo')
	).then(cb, cb);
    }
    CatIdentityProvider.prototype.getDistanceFrom = function(lat, lon) {
	function deg2rad (deg) {
	    return deg * ((1 / 180) * Math.PI);
	}
	var cb = function(ret) {
	    if (Array.isArray(ret)) {
		var res = [];
		ret.forEach(function(cur, idx) {
		    var lat2 = deg2rad(cur.lat);
		    var lat1 = deg2rad(lat);
		    var lon2 = deg2rad(cur.lon);
		    var lon1 = deg2rad(lon);
		    res.push(
			Math.acos(
			    (Math.sin(lat1) * Math.sin(lat2)) +
				(Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1))
			) * 6371
		    );
		});
		return res;
	    } else {
		return [Infinity];
	    }
	}
	return $.when(this.getGeo()).then(cb, cb);
    }
    CatIdentityProvider.prototype.getProfiles = function(returnArray) {
	// consider caching these objects
	return CatProfile.getProfilesByIdPEntityID(this.cat, this.id, this.lang, returnArray);
    }
    CatIdentityProvider.prototype.hasSearchMatch = function(search) {
	if (typeof search !== 'string') {
	    return false;
	}
	var keywords = search.toLowerCase().trim().split(/[\s,]+/);
	var cb = function(ret) {
	    if (!!!ret) {
		return false;
	    }
	    return keywords.reduce(function(carry, item) {
		return carry && (!item || ret.toLowerCase().indexOf(item) !== -1);
	    }, true);
	}
	return $.when(
	    this.getTitle()
	).then(cb, cb);
    }

    // ***** CAT Profile *****
    CatProfile = function(cat, idpid, profid, lang) {
	this.cat = cat;
	this.idp = idpid;
	this.id = profid;
	this.lang = lang;
    }
    // not an instance method!
    CatProfile.getProfilesByIdPEntityID = function(cat, idpid, lang, returnArray) {
	var cb = function(ret) {
	    if (Array.isArray(ret)) {
		var profiles = !!!returnArray ? {} : [];
		for (var idx=0; idx < ret.length; idx++) {
		    if (!!ret[idx] && ('id' in ret[idx]) && parseInt(ret[idx].id)) {
			var prof = new CatProfile(cat, idpid, parseInt(ret[idx].id), lang);
			if (!!!returnArray) {
			    profiles[ret[idx].id] = prof;
			} else {
			    profiles.push(prof);
			}
		    }
		}
		return profiles;
	    } else {
		return null;
	    }
	}
	return $.when(
	    cat.listProfiles(idpid, lang)
	).then(cb, cb);
    }
    // PHP (wrong?): getRawAttributes()
    CatProfile.prototype.getRaw = function() {
	var $prof = this;
	var cb = function (ret) {
	    if (Array.isArray(ret)) {
		return ret.find(function(cur, idx) {
		    return !!cur && parseInt(cur.id) === $prof.id;
		});
	    } else {
		return null;
	    }
	}
	return $.when(
	    this.cat.listProfiles(this.idp, this.lang)
	).then(cb, cb);
    }
    // PHP (wrong?): getRaw()
    CatProfile.prototype.getRawAttributes = function() {
	return this.cat.profileAttributes(this.id, this.lang);
    }
    // not an instance method!
    CatProfile.getRawDevicesByProfileID = function(cat, profid, lang) {
	// simulated 'this' obj, having only what _getProp() and getRawAttributes() access
	var fake_this = { cat: cat,
			  id: profid,
			  lang: lang }
	return CatProfile.prototype._getProp.call(fake_this,
						  CatProfile.prototype.getRawAttributes,
						  'devices');
    }
    CatProfile.prototype._getProp = function(rawFunc, prop) {
	var cb = function(ret) {
	    if (typeof prop === 'undefined') {
		return null;
	    }
	    if (!!ret &&
		(prop in ret)) {
		return ret[prop];
	    } else {
		return null;
	    }
	}
	return $.when(
	    rawFunc.call(this)
	).then(cb, cb);
    }
    CatProfile.prototype.getProfileID = function() {
	return this.id;
    }
    CatProfile.prototype.getIdpID = function() {
	return this.idp;
    }
    CatProfile.prototype.getDisplay = function() {
	var idpObj = this.getIdentityProvider();
	var cb = function(prof_display, idp_display) {
	    if (prof_display) {
		return prof_display;
	    } else if (idp_display) {
		return idp_display;
	    } else {
		return null;
	    }
	}
	return $.when(
	    this._getProp(this.getRaw, 'display'),
	    idpObj.getDisplay()
	).then(cb, cb);
    }
    /*
     * omitting #hasLogo() and #getIdentityProviderName() because these
     * belong in the IdentityProvider class.
     */
    CatProfile.prototype.getLocalEmail = function() {
	return this._getProp(this.getRawAttributes, 'local_email');
    }
    CatProfile.prototype.getLocalPhone = function() {
	return this._getProp(this.getRawAttributes, 'local_phone');
    }
    CatProfile.prototype.getLocalUrl = function() {
	return this._getProp(this.getRawAttributes, 'local_url');
    }
    CatProfile.prototype.getDescription = function() {
	return this._getProp(this.getRawAttributes, 'description');
    }
    CatProfile.prototype.getDevices = function() {
	// consider caching these objects
	var $prof = this;
	var cb = function(ret) {
	    if (Array.isArray(ret)) {
		var devices = {};
		ret.forEach(function(cur, idx) {
		    if ((!!cur.redirect ||
			 (('status' in cur) &&
			  (cur.status >= 0))) &&
			(!("options" in cur) || !!!cur.options.hidden)) {
			devices[cur.id] = new CatDevice($prof.cat,
							$prof.idp,
							$prof.id,
							cur.id,
							$prof.lang);
		    }
		});
		return devices;
	    } else {
		return null;
	    }
	}
	return $.when(
	    this._getProp(this.getRawAttributes, 'devices')
	).then(cb, cb);
    }
    CatProfile.prototype.hasSupport = function() {
	var cb = function(local_email,
			  local_phone,
			  local_url) {
	    return !!local_email ||
		!!local_phone ||
		!!local_url;
	}
	return $.when(
	    this.getLocalEmail(),
	    this.getLocalPhone(),
	    this.getLocalUrl()
	).then(cb, cb);
    }
    CatProfile.prototype.getIdentityProvider = function() {
	return new CatIdentityProvider(this.cat, this.idp, this.lang);
    }
    CatProfile.prototype.isRedirect = function() {
	var cb = function(ret) {
	    var deferreds = [];
	    for (var devid in ret) {
		deferreds.push(ret[devid].isProfileRedirect());
	    }
	    var cb = function() {
		var args = Array.prototype.slice.call(arguments);
		// Return value: true if the callback function returns
		// a truthy value for any array element; otherwise,
		// false.
		return args.some(function(cur) {
		    return cur;
		});
	    }
	    return $.when.apply($, deferreds)
		.then(cb, cb);
	}
	return $.when(
	    this.getDevices()
	).then(cb, cb);
    }

    // ***** CAT Device *****
    var USER_AGENTS = {
	'vista': [/Windows NT 6[._]0/],
	'w7': [/Windows NT 6[._]1/],
	'w8': [/Windows NT 6[._][23]/],
	'w10': [/Windows NT 10/],
	'mobileconfig-56': [/\((iPad|iPhone|iPod);.*OS [56]_/],
	'mobileconfig': [/\((iPad|iPhone|iPod);.*OS [7-9]/, /\((iPad|iPhone|iPod);.*OS 1[0-1]/],
	'mobileconfig12': [/\((iPad|iPhone|iPod);.*OS 1[2-9]/],
	'apple_lion': [/Mac OS X 10[._]7/],
	'apple_m_lion': [/Mac OS X 10[._]8/],
	'apple_mav': [/Mac OS X 10[._]9/],
	'apple_yos': [/Mac OS X 10[._]10/],
	'apple_el_cap': [/Mac OS X 10[._]11/],
	'apple_sierra': [/Mac OS X 10[._]12/],
	'apple_hi_sierra': [/Mac OS X 10[._]13/],
	'apple_mojave': [/Mac OS X 10[._]1[4-9]/, /Mac OS X 10[._][2-9][0-9]/],
	'linux': [/Linux(?!.*Android)/],
	'chromeos': [/CrOS/],
	'android_43': [/Android 4[._]3/],
	'android_kitkat': [/Android 4[._][4-9]/],
	'android_lollipop': [/Android 5/],
	'android_marshmallow': [/Android 6/],
	'android_nougat': [/Android 7/],
	'android_oreo': [/Android 8/],
	'android_pie': [/Android 9/],
	'android_q': [/Android [1-9][0-9]/],
	'android_legacy': [/Android/],
	'__undefined__': [ new RegExp('') ]
    }
    var DEVICE_GROUPS = {
	'Windows': [/^w[0-9]/, /^vista$/],
	'Apple': [/^apple/, /^mobileconfig/],
	'Android': [/^android/],
	'Linux': [/^linux/],
	'Other': [ new RegExp('') ]
    }
    CatDevice = function(cat, idpid, profid, devid, lang) {
	this.cat = cat;
	this.idp = idpid;
	this.profid = profid;
	this.id = devid;
	this.lang = lang;
    }
    CatDevice.prototype.USER_AGENTS = USER_AGENTS;
    CatDevice.prototype.DEVICE_GROUPS = DEVICE_GROUPS;
    // not an instance method!
    CatDevice.loadDevices = function(cat, idpid, profid, lang) {
	var cb = function(devices_augmented,
			  devices) {
	    var devs_array,
		devs_obj = {};
	    if (Array.isArray(devices_augmented) &&
		devices_augmented.length) {
		devs_array = devices_augmented;
	    }
	    else if (Array.isArray(devices) &&
		     devices.length) {
		devs_array = devices;
	    } else {
		return null;
	    }
	    for (var idx = 0; idx < devs_array.length; idx++) {
		if ('id' in devs_array[idx]) {
		    devs_obj[devs_array[idx].id] = devs_array[idx];
		}
	    }
	    return devs_obj;
	}
	return $.when(
	    CatProfile.getRawDevicesByProfileID(cat, profid, lang),
	    cat.listDevices(profid, lang)
	).then(cb, cb);
    }
    // not an instance method!
    CatDevice.groupDevices = function(devices) {
	if (!!!devices) {
	    // return a (resolved) promise for consistency
	    return $.when().then(function() {
		return null;
	    });
	}
	var result = {},
	    k;
	for (k in CatDevice.prototype.DEVICE_GROUPS) {
	    result[k] = [];
	}
	var _devices = [],
	    deferreds = [],
	    devices_keys = Object.keys(devices);
	for (var idx in devices_keys) {
	    idx = devices_keys[idx];
	    if (!('getStatus' in devices[idx]) ||
		!('getGroup' in devices[idx])) {
		continue;
	    }
	    _devices.push(idx);
	    deferreds.push(devices[idx].getStatus());
	}
	var cb = function() {
	    var args = Array.prototype.slice.call(arguments);
	    for (var idx=0; idx < _devices.length; idx++) {
		var group = devices[_devices[idx]].getGroup(),
		    status = args[idx];
		if (status != 0) {
		    continue;
		}
		if (group != null) {
		    result[group].push(devices[_devices[idx]]);
		}
	    }
	    for (k in result) {
		if (!result[k].length) {
		    delete result[k];
		}
	    }
	    return result;
	}
	return $.when.apply($, deferreds)
	    .then(cb, cb);
    }
    // not an instance method!
    CatDevice.guessDeviceID = function(userAgent, deviceIDs) {
	var UAs = CatDevice.prototype.USER_AGENTS;
	deviceIDs = Array.isArray(deviceIDs) ? deviceIDs : Object.keys(UAs);
	for (var idx=0; idx < deviceIDs.length; idx++) {
	    var device_patterns = Array.isArray(UAs[deviceIDs[idx]]) ?
		UAs[deviceIDs[idx]] : [];
	    for (var regex in device_patterns) {
		if (device_patterns[regex].test(userAgent)) {
		    return deviceIDs[idx];
		}
	    }
	}
	return null;
    }
    CatDevice.prototype.detectDeviceID = function(deviceIDs) {
	var UAs = this.USER_AGENTS;
	deviceIDs = Array.isArray(deviceIDs) ? deviceIDs : Object.keys(UAs);
	var cb = function(dev_id_obj) {
	    return !!dev_id_obj && !!dev_id_obj.id &&
		dev_id_obj.id ||
		deviceIDs.pop(); // assume last resort at the end
	}
	return $.when(
	    this.cat.detectOS()
	).then(cb, cb);
    }
    CatDevice.prototype.getDeviceID = function() {
	return this.id;
    }
    CatDevice.prototype.getProfileID = function() {
	return this.profid;
    }
    // CatProfile.prototype.getIdpID = function() {
    // 	return this.idp;
    // }
    CatDevice.prototype.getRaw = function() {
	var $dev = this;
	var cb = function(ret) {
	    if (!!ret &&
		($dev.id in ret)) {
		return ret[$dev.id];
	    } else {
		return null;
	    }
	}
	return $.when(
	    CatDevice.loadDevices(this.cat, this.idp, this.profid, this.lang)
	).then(cb, cb);
    }
    CatDevice.prototype._getProp = function(rawFunc, prop, propNested) {
	var cb = function(ret) {
	    if (typeof prop === 'undefined') {
		return null;
	    }
	    if (!!ret &&
		(prop in ret)) {
		if (typeof propNested === 'undefined') {
		    return ret[prop];
		}
		if (!!ret[prop] &&
		    (propNested in ret[prop])) {
		    return ret[prop][propNested];
		} else {
		    return null;
		}
	    } else {
		return null;
	    }
	}
	return $.when(
	    rawFunc.call(this)
	).then(cb, cb);
    }
    CatDevice.prototype.getDisplay = function() {
	var cb = function(is_profileredirect,
			  device_display) {
	    if (is_profileredirect) {
		return 'External';
	    }
	    return device_display;
	}
	return $.when(
	    this.isProfileRedirect(),
	    this._getProp(this.getRaw, 'display')
	).then(cb, cb);
    }
    CatDevice.prototype.getStatus = function() {
	return this._getProp(this.getRaw, 'status');
    }
    CatDevice.prototype.getRedirect = function() {
	return this._getProp(this.getRaw, 'redirect');
    }
    CatDevice.prototype.getEapCustomText = function() {
	return this._getProp(this.getRaw, 'eap_customtext');
    }
    CatDevice.prototype.getDeviceCustomText = function() {
	return this._getProp(this.getRaw, 'device_customtext');
    }
    CatDevice.prototype.getMessage = function() {
	return this._getProp(this.getRaw, 'message');
    }
    CatDevice.prototype.getDeviceInfo = function() {
	var $dev = this;
	var cb = function(is_redirect) {
	    if (is_redirect) {
		// Seems like CAT doesn't answer this one on redirects...
		return null;
	    }
	    return $dev.cat.deviceInfo($dev.profid, $dev.id, $dev.lang);
	}
	return $.when(
	    this.isRedirect()
	).then(cb, cb);
    }
    CatDevice.prototype.getDownload = function(dryrun) {
	var $dev = this,
	    dryrun = !!dryrun;
	var cb = function(is_redirect,
			  device_redirect) {
	    if (is_redirect) {
		return device_redirect;
	    }
	    return $dev.cat.downloadInstaller($dev.profid, $dev.id, $dev.lang, dryrun);
	}
	return $.when(
	    this.isRedirect(),
	    this.getRedirect()
	).then(cb, cb);
    }
    CatDevice.prototype.getDownloadLink = function() {
	return this.getDownload(true);
    }
    CatDevice.prototype.isSigned = function() {
	var cb = function(ret) {
	    return !!ret;
	}
	return this._getProp(this.getRaw, 'options', 'sign')
	    .then(cb, cb);
    }
    CatDevice.prototype.isRedirect = function() {
	var cb = function(ret) {
	    return !!ret;
	}
	return this._getProp(this.getRaw, 'redirect')
	    .then(cb, cb);
    }
    CatDevice.prototype.isProfileRedirect = function() {
	var $dev = this;
	var cb = function(device_redirect,
			  device_display) {
	    // '0' is the fake device-id returned by profileAttributes
	    // for a profile-induced redirect -> we do need to match it
	    // '__undefined__' is our fake device-id for the last
	    // resort match in USER_AGENTS -> not sure if we need it here...
	    return ($dev.id == '__undefined__' ||
		    $dev.id === '0') && !!!device_display && device_redirect;
	}
	return $.when(
	    this.getRedirect(),
	    this._getProp(this.getRaw, 'display')
	).then(cb, cb);
    }
    CatDevice.prototype.getGroup = function() {
	var dev_groups = this.DEVICE_GROUPS;
	for (var group in dev_groups) {
	    var device_patterns = Array.isArray(dev_groups[group]) ?
		dev_groups[group] : [];
	    for (var regex in device_patterns) {
		if (device_patterns[regex].test(this.getDeviceID())) {
		    return group;
		}
	    }
	}
	// failsafe?
	return 'Other';
    }

    // module constructor
    return function() {
	var api_instance = CAT.new_with_array(arguments);
	function prepend_api() {
	    var args = Array.from_arguments.apply(null, arguments);
	    args.unshift(this.API);
	    return args;
	}
	return {
	    API: api_instance,
	    reset_api: function() {
		return this.API = CAT.new_with_array(arguments);
	    },
	    IdentityProvider: function() {
		return CatIdentityProvider
		    .new_with_array(prepend_api.apply(this, arguments));
	    },
	    Profile: function() {
		return CatProfile
		    .new_with_array(prepend_api.apply(this, arguments));
	    },
	    Device: function() {
		return CatDevice
		    .new_with_array(prepend_api.apply(this, arguments));
	    }
	}
    }
}));
