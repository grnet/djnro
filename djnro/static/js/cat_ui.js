;(function(root, factory) {
    var deps = ['jquery', 'history', 'nprogress', 'querystring',
		'jquery.base64',
		'Array.isArray'];
    if (typeof define === 'function' && define.amd) {
	define(deps, function() {
	    // return (root.ConfigurationAssistantToolUI = factory.apply(root, arguments);
	    return factory.apply(root, arguments);
	});
    } else if (typeof module === 'object' && module.exports) {
	var req_deps = (function() {
	    var deps = [];
	    for (var i = 0; i < arguments.length; i++) {
		deps.push(require(dep));
	    }
	    return deps;
	}.apply(null, deps));
	// module.exports = (root.ConfigurationAssistantToolUI = factory.apply(root, req_deps));
	module.exports = factory.apply(root, req_deps);
    } else {
	root.ConfigurationAssistantToolUI = factory.call(root, root.jQuery);
    }

}(this, function($, History, NProgress, queryString) {
    'use strict';

    var root = this;
    var cuopts = {};
    var CAT, catPrototypes = {};

    // pub/sub
    var o = $({});
    $.subscribe = function() {
	o.on.apply(o, arguments);
    }
    $.unsubscribe = function() {
	o.off.apply(o, arguments);
    }
    $.publish = function() {
	o.trigger.apply(o, arguments);
    }

    if (!String.prototype.nformat) {
    	Object.defineProperty(String.prototype, "nformat", {
    	    value: function() {
	// String.prototype.nformat = function() {
		var args = Array.prototype.slice.call(arguments),
		    kwargs = {};
		if (args[0] instanceof Object) {
		    kwargs = args.shift();
		}
		return this.replace(/{(\w+)}/g, function(match, number_or_name) {
		    if (number_or_name in kwargs) {
			return kwargs[number_or_name];
		    }
		    else if (number_or_name in args) {
			return args[number_or_name];
		    }
		    else {
			return match;
		    }
		});
	    }
	});
    }

    function selector_encode(obj) {
	var btoa = root.btoa || $.base64.btoa;
	return btoa(JSON.stringify(obj)).replace(/=/g, '_');
    }
    function selector_decode(hash) {
	var atob = root.atob || $.base64.atob;
	return JSON.parse(atob(hash.replace(/_/g, '=')));
    }

    var getQueryParameters,
	getQueryString;
    (function() {
	var qs = queryString || root.queryString,
	    opts = {
		sort: false,
		multiVal: false
	    };
	getQueryParameters = function(str) {
	    return qs.parse(str, opts);
	}
	getQueryString = function(obj) {
	    return qs.stringify(obj, opts);
	}
    }());

    var hstate = {
	prefix: '#!',
	init: function() {
	    var self = this,
		history = typeof History != "undefined" ? History : root.history;
	    if (history.emulate) {
		self.prefix = '/';
		history.setup(undefined, '!');
	    }
	},
	// hashRegExp: /^(?:[^#]*)(?:#?(.*))$/,
	fromFragment: function (_hash) {
	    var self = this, location, hash,
		history = typeof History != "undefined" ? History : root.history;
	    if (history.emulate) {
		location = history.location;
		hash = _hash || location.pathname;
		if (hash.indexOf(self.prefix) == 0) {
		    hash = hash.substr(self.prefix.length);
		}
	    } else {
		location = root.location;
		var hash = _hash || location.hash;
		if (hash) {
		    var hashParts = hash.match(/^(#!?)(.*)$/);
		    if (hashParts !== null && hashParts.length == 3) {
			self.prefix = hashParts[1];
			hash = hashParts[2];
		    } else {
			return {};
		    }
		}
	    }
	    return getQueryParameters(hash);
	},
	toFragment: function(obj, act, trigger, $el) {
	    var self = this,
		history = typeof History != "undefined" ? History : root.history;

	    var hash = getQueryString(obj);
	    hash = self.prefix + hash;

	    if (act == 'replace') {
		act = 'replaceState';
	    } else {
		act = 'pushState';
	    }

	    // just force boolean
	    trigger = Boolean(typeof trigger == "undefined" ? true : trigger);

	    var scrollV, scrollH,
		location = history.emulate ? history.location : root.location;

	    var same_hash = history.emulate ?
		location.pathname == hash :
		location.hash == hash;
	    if (same_hash) {
		return false;
	    }
	    if (hash == self.prefix && !history.emulate) {
		hash = '';
	    }

	    if (act in history) {
		// emulated history state mgmt
		if (history.emulate) {
		    history[act](obj, null, hash);
		// native history state mgmt
		} else {
		    history[act](obj, null, location.pathname + location.search + hash);
		}
	    }
	    // history state fallback: hashchange 
	    else {
		// Prevent scrolling by storing the page's current scroll offset
		scrollV = document.body.scrollTop;
		scrollH = document.body.scrollLeft;

		location.hash = hash;

		// Restore the scroll offset, should be flicker free
		document.body.scrollTop = scrollV;
		document.body.scrollLeft = scrollH;
	    }

	    if (trigger) {
		$(root).trigger(events.history_change, [$el]);
	    }
	    return true;
	}
    }

    var controllers = {};

    controllers.tostate = function(evt, state, $el) {
	var trigger_popstate = true;
	var hard;
	if (typeof state === 'undefined') {
	    state = {};
	}
	var prev_state = hstate.fromFragment();
	if ('_act' in state) {
	    hard = (state._act == 'replace') && 'replace';
	    delete state._act;
	}
	var implied_act = evt.type.split('_', 2);
	var ordered_keys = pubsub_cats_ordered;
	if (implied_act.length > 1 && implied_act[1] == 'remove' && (implied_act[0] in state)) {
            for (var _i=0; _i < ordered_keys.length && implied_act[0] != ordered_keys[_i];
		 _i++); // empty statement
            if (_i < ordered_keys.length) {
		for (var i=_i; i < ordered_keys.length; i++) {
		    if (ordered_keys[i] in prev_state) {
			delete state[ordered_keys[i]];
		    }
		}
            }
	}
	var _changed = false;
	for (var k in state) {
	    if (!(k in prev_state) || prev_state[k] != state[k]) {
		_changed = true;
	    }
	}
	for (var _k in prev_state) {
	    if (!(_k in state)) {
		if (ordered_keys.indexOf(_k) == -1) {
		    state[_k] = prev_state[_k];
		} else {
		    _changed = true;
		}
	    }
	}
	if (_changed) {
	    hstate.toFragment(state, hard, trigger_popstate, $el);
	}
    }

    function strip_namespace(id) {
	return id.split('.')[0];
    }

    var selectors = {
	toggles_modal_has_cidp_id: '[data-toggle="modal"][data-catidp]',
	toggles_modal_with_cidp_id: '[data-toggle="modal"][data-catidp="{cidp}"]',
	toggles_tab_with_cprof_id: '[data-toggle="tab"][data-catprof="{cprof}"]',
	changes_cdev_with_cprof_cdev_ids_ctx_catprofpane: '[data-catprofpane="{cprof}"] [data-catdev="{cdev}"]',
	changes_cdev_nomatch_with_cprof_id: '[data-catprofpane="{cprof}"] [data-catui="device-no-match"]',
	catui_container_logo: '[data-catui="container-logo"]',
	catui_container_support: '[data-catui="container-support"]',
	inst_list_ul: 'ul.insts',
	cat_modal: '.modal#catModal',
	catui_profile_select_container: '[data-catui="profile-select-container"]',
	toggles_tab_has_catprof_id: '[data-toggle="tab"][data-catprof]',
	target_catprofpane_with_cprof_id: '[data-catprofpane="{cprof}"]',
	catui_institution: '[data-catui="institution"]',
	catui_container_support_contact: '[data-catui="support-contact-container"]',
	catui_profiles_container: '[data-catui="profiles-container"]',
	catui_profile_container_template: '[data-catui="profile-container-template"]',
	catui_profile_loading_placeholder: '[data-catui="profile-loading-placeholder"]',
	catui_profile_load_error: '[data-catui="profile-load-error"]',
	catui_profile_description: '[data-catui="profile-description"]',
	catui_profile_container_with_catprofpane_id: '[data-catui="profile-container"][data-catprofpane="{cprof}"]',
	catui_device_container: '[data-catui="device-container"]',
	catui_device_loading_placeholder: '[data-catui="device-loading-placeholder"]',
	changes_cdev_has_cdev_id_ctx_devicelist_container: '[data-catui="devicelist-container"] [data-catdev]',
	changes_cdev_with_cdev_id: '[data-catdev="{cdev}"]',
	changes_cdev_has_cdev_id: '[data-catdev]',
	changes_cdev_nomatch: '[data-catui="device-no-match"]',
	catui_device_no_match: '[data-catui="device-no-match"]',
	catui_devicelist_container: '[data-catui="devicelist-container"]',
	toggles_collapse_noanimation: '[data-toggle="collapse-noanimation"]',
	catui_device_deviceinfo: '[data-catui="device-deviceinfo"]',
	catui_profile_container: '[data-catui="profile-container"]',
	catui_device_redirecturl: '[data-catui="device-redirecturl"]',
	catui_dltxt_init: '[data-catui-dltxt="init"]',
	catui_device_download: '[data-catui="device-download"]',
	catui_device_redirectmessage: '[data-catui="device-redirectmessage"]',
	catui_device_message: '[data-catui="device-message"]',
	catui_cat_api_tou: '[data-catui="cat-api-tou"]',
	catui_dltxt_generate: '[data-catui-dltxt="generate"]',
	catui_dltxt_download: '[data-catui-dltxt="download"]',
	catui_dltxt_fail: '[data-catui-dltxt="fail"]',
	catui_device_load_error: '[data-catui="device-load-error"]'
    }

    var events = {
	history_change: '{0}.cat_ui'
	    .nformat('onpopstate' in root ? 'popstate' : 'hashchange'),
	click: 'click.cat_ui',
	cidp_disable_selector: 'cidp_disable_selector.cat_ui',
	cidp_bind_selector: 'cidp_bind_selector.cat_ui',
	cidp_unbind_selector: 'cidp_unbind_selector.cat_ui'
    }

    var pubsub_cats_ordered = ['cidp', 'cprof', 'cdev'],
	pubsubs = function() {
	    var ret = {},
		directions = ['fromstate', 'tostate'],
		triggers = ['change', 'remove'];
	    for (var i_ps=0; i_ps < arguments.length; i_ps++) {
		ret[arguments[i_ps]] = {}
		for (var i_t=0; i_t < triggers.length; i_t++) {
		    ret[arguments[i_ps]][triggers[i_t]] = {};
		    for (var i_d=0; i_d < directions.length; i_d++) {
			ret[arguments[i_ps]][triggers[i_t]][directions[i_d]] =
			    '{0}_{1}.cat_ui.{2}'
			    .nformat(arguments[i_ps],
				     triggers[i_t],
				     directions[i_d]);
		    }
		}
	    }
	    return ret;
	}.apply(null, pubsub_cats_ordered);

    controllers.fromstate = function(evt, $el) {
	var state = hstate.fromFragment(),
	    pairs = {
		cidp:  { obj: views.cidp.obj  },
		cprof: { obj: views.cprof.obj },
		cdev:  { obj: views.cdev.obj  }
	    }
	for (var key in pairs) {
	    var stateChange = 0;
	    if (!(key in state)) {
		if (typeof pairs[key].obj !== "undefined") {
		    stateChange = 2;
		}
	    }
	    else if (typeof pairs[key].obj === "undefined" ||
		     (state[key] != pairs[key].obj.id)) {
		stateChange = 1;
	    }
	    // special case: device id (cdev) may be common across objects
	    // else if (key == 'cdev' && (pairs[key].obj instanceof catPrototypes.Device)) {
	    // 	if (('cprof' in state) &&
	    // 	    state.cprof != pairs[key].obj.getProfileID()) {
	    // 	    stateChange = 1;
	    // 	}
	    // }		     
	    if (stateChange === 0) {
		continue;
	    }
	    switch (key) {
	    case 'cidp':
		if (stateChange === 2) {
		    views.cidp.obj = undefined;
		    // delete state.cidp;
		    $.publish(pubsubs.cidp.remove.fromstate, [state, $el]);
		} else {
		    return $.publish(pubsubs.cidp.change.fromstate, [state, $el]);
		}
		// fallthrough if stateChange === 2
	    case 'cprof':
		if (stateChange === 2) {
		    if (key != 'cprof') {
			// don't blindly set _catProf (last catProf), but push
			// catProf.id in front of _catProf and add catProf to
			// _catProfO
			if (!!views.cprof.obj) {
			    var idx;
			    if ((idx = views.cprof.prev_stack.indexOf(views.cprof.obj.id)) != -1) {
				views.cprof.prev_stack.splice(idx, 1);
			    } else {
				views.cprof.prev_obj[views.cprof.obj.id] = views.cprof.obj;
			    }
			    views.cprof.prev_stack.unshift(views.cprof.obj.id);
			}
			// delete state.cprof;
			state._act = 'replace';
			$.publish(pubsubs.cprof.remove.tostate, [state, $el]);
		    }
		    views.cprof.obj = undefined;
		} else {
		    if (!('cidp' in state)) {
		    	console.warn('have cprof but no cidp!!');
			state._act = 'replace';
		    	return $.publish(pubsubs.cprof.remove.tostate, [state, $el]);
		    }
		    return $.publish(pubsubs.cprof.change.fromstate, [state, $el]);
		}
		// fallthrough if stateChange === 2
	    case 'cdev':
		if (stateChange === 2) {
		    if (key != 'cdev') {
			views.cdev.prev_obj = !!views.cdev.obj &&
			    views.cdev.obj || views.cdev.prev_obj;
			// delete state.cdev;
			state._act = 'replace';
			$.publish(pubsubs.cdev.remove.tostate, [state, $el]);
		    }
		    views.cdev.obj = undefined;
		} else {
		    if (!('cprof' in state)) {
			console.warn('have cdev but no cprof!!');
			state._act = 'replace';
			return $.publish(pubsubs.cdev.remove.tostate, [state, $el]);
		    }
		    return $.publish(pubsubs.cdev.change.fromstate, [state, $el]);
		}
		break;
	    }
	}
	return this;
    }

    var handlers = {
	// light-weight bootstrap collapsible without animation
	bs_collapsible_noanimation: function(evt) {
	    evt.preventDefault();
	    var id = $(this).attr('data-target'),
		collapsed_init = $(this).hasClass('collapsed'),
		aria_expanded = collapsed_init ? 'true' : 'false';
	    $(this).toggleClass('collapsed')
		.attr('aria-expanded', aria_expanded)
		.closest('.panel-heading')
		.siblings(id)
		.toggleClass('in')
		.attr('aria-expanded', aria_expanded);
	    return this;
	},
	// usability enhancement for accordion collapsibles (without animation)
	// propagate clicks to the device group/device info headings, device
	// selectors from their container elements
	bs_collapsible_click_propagate: function (evt) {
	    var $that = $(this)
		.find('{0},{1}'.nformat(
		    selectors.toggles_collapse_noanimation,
		    selectors.changes_cdev_has_cdev_id)
		     );
	    if ($that.length > 0 &&
		evt.target !== $that.get(0) &&
		$that.find(evt.target).length == 0) {
		return $that.trigger(events.click);
	    }
	    return this;
	},
	// hiding other device groups upon device group selection
	// workaround for bootstrap collapse data-parent not working
	bs_collapsible_hide_other: function (evt) {
	    $(this)
		.parent('.panel-heading')
		.siblings($(this).data('target'))
		.siblings('.panel-collapse.in')
		.removeClass('in');
	    return this;
	},
	// buttons move around as they grow bigger in focus state
	// click may fire on a different element or not at all
	// thus we trigger a "composite click" on the element where mousedown fired
	// implicitly this means releasing mouse outside the original button (but still inside
	// ul.insts) will still fire click -- which is what we usually want
	// this seems to work fine with touch clicks, but needs more testing
	// ref:
	// https://bugzilla.mozilla.org/show_bug.cgi?id=326851
	composite_click_optimized: function (evt) {
	    // only react on "left-click"
	    if (evt.type != 'focusin' && evt.which != 1) {
		return this;
	    }
	    var buttonPressed = evt.type == 'mouseup' ? $(this).data('_buttonpressed') :
		$(evt.target).closest(selectors.toggles_modal_has_cidp_id);
	    switch (evt.type) {
	    case 'mouseup':
		if (buttonPressed instanceof $) {
		    $(this).removeData('_buttonpressed');
		    buttonPressed.trigger(events.click);
		}
		break;
	    case 'mousedown':
		if (buttonPressed.length == 1) {
		    $(this).data('_buttonpressed', buttonPressed);
		}
		// fall-through
	    case 'focusin':
		if (buttonPressed.length == 1) {
    		    var cidp = parseInt(buttonPressed.data('catidp'));
    		    if (!!cidp) {
    			// optimization: pre-fetching on mousedown/focus
    			CAT.API.listProfiles(cidp);
    		    }
		}
    		break;
	    }
	    return this;
	},
	bs_modal_hidden: function(evt) {
	    var state = hstate.fromFragment();
	    $.publish(pubsubs.cidp.remove.tostate, [state]);
	    // bootstrap transitions (.modal.fade) use timers (conditionally) which
	    // may clash with rapid state transitions
	    // workaround: ensure any orphan backdrops are removed after modal is hidden
	    if ($(this).hasClass('fade')) {
		$('body > .modal-backdrop.fade').remove();
	    }
    	    return this;
	}
    }

    var exthandlers = {
	cidp_bind_selector: $.noop,
	cidp_unbind_selector: $.noop,
	modal_title: function(title) { return title; }
    }

    var views = {};

    views.cidp = {
	handle: function(evt) {
	    var self = views.cidp;
	    switch (evt.type) {
	    case strip_namespace(events.click):
		evt.preventDefault();
		if (!('namespace' in evt) ||
		    evt.namespace.indexOf('cat_ui') == -1) {
		    break;
		}
		var state = hstate.fromFragment(),
		key = 'cidp',
		val = $(this).attr('data-catidp');
		state[key] = val;
		// state._act = 'push';
		return $.publish(pubsubs.cidp.change.tostate,
				 [state, $(this)]);
		break;
	    case strip_namespace(events.cidp_disable_selector):
		var $el = $(this);
		$el.trigger(events.cidp_unbind_selector);
		$el.attr('data-catidp', null).removeData('catidp');
		break;
	    case strip_namespace(events.cidp_bind_selector):
		var $el = $(this),
		catIdpID = parseInt($el.data('catidp')),
		_cidp = $el.data('_catidp');
		if (!!!catIdpID) {
		    return false;
		}
		$el.attr({'data-toggle': 'modal',
			  'data-target': 'catModal'});
		if (!(_cidp instanceof catPrototypes.IdentityProvider)) {
		    _cidp = CAT.IdentityProvider(catIdpID);
		    $el.data('_catidp', _cidp);
		}
		$el.attr('href',
			 '#cat-{0}'.nformat(
			     selector_encode({cidp: catIdpID})
			 )
			);
		$el.on(events.click, views.cidp.handle);
		exthandlers.cidp_bind_selector.call(this);
		break;
	    case strip_namespace(events.cidp_unbind_selector):
		var $el = $(this),
		catIdpID = parseInt($el.data('catidp'));
		if (!!!catIdpID) {
		    return false;
		}
		$el.removeData('_catidp');
		$el.attr({'data-toggle': null,
			  'data-target': null})
		    .removeData('toggle target');
		var href = $(this).attr('href');
		if (href && href.indexOf('#cat-') == 0) {
		    $(this).attr('href', null);
		}
		$el.off(events.click);
		exthandlers.cidp_unbind_selector.call(this);
		break;
	    }
	    return this; // jQuery chaining
	},
	subscriber: function(evt, state, $el) {
	    var self = views.cidp;
	    switch (evt.type) {
	    case strip_namespace(pubsubs.cidp.remove.fromstate):
		$(selectors.cat_modal).modal('hide');
		if ($el instanceof $ && $el.length == 1) {
		    $el.focus();
		} else if ('element' in self && $(self.element) instanceof $) {
		    $(self.element).focus();
		}
		break;
	    case strip_namespace(pubsubs.cidp.change.fromstate):
		if (!(state instanceof Object)) {
		    return false;
		}
		if ($el instanceof $) {
		    self.element = $el.get(0);
		} else {
		    $el = $(selectors.toggles_modal_with_cidp_id.nformat(state));
		    if ($el.length != 1) {
			return false;
		    }
		    self.element = $el.get(0);
		}
		self.main();
		break;
	    }
	    return this;
	},
	obj: undefined,
	progress: function() {
	    if (typeof NProgress === 'function') {
		return NProgress;
	    } else if ('NProgress' in root) {
		return root.NProgress;
	    } else {
		return {
		    start: $.noop,
		    done: $.noop
		}
	    }
	},
	main: function() {
	    var self = this;
	    var cidp = $(self.element).data('_catidp');
	    self.obj = (cidp instanceof catPrototypes.IdentityProvider) ?
		cidp :
		CAT.IdentityProvider(parseInt($(self.element).data('catidp')));
	    $(self.element).data('_catidp',
				 self.obj);
	    self.progress().start();
	    return $.when(
		self.obj.getProfiles(true)
	    ).then(self.main_cb, self.main_cb);
	},
	main_cb: function(profiles) {
	    var self = views.cidp;
	    if (!!!self.obj) {
		return null;
	    }
	    if (profiles === null ||
		!Array.isArray(profiles) ||
		profiles.length == 0) {
		$(self.element).trigger(events.cidp_disable_selector);
		$.publish(pubsubs.cidp.remove.tostate,
			  [$.extend({}, hstate.FromFragment(),
				    {_act: 'replace'})]);
		self.progress().done();
		return false;
	    }
	    var profiles_byid = self.setup_profile_selectors(profiles);
	    self.select_profile(profiles, profiles_byid);
	    $.when(
		self.obj.getDisplay(),
		self.obj.getIcon()
	    ).then(self.setup_title_icon, self.setup_title_icon);
	    self.progress().done();
	    $(selectors.cat_modal)
		.modal('show');
	},
	setup_profile_selectors: function(profiles) {
	    var self = this;
	    self.$profsel_container = $(selectors.cat_modal)
		.find(selectors.catui_profile_select_container);
	    var $profsel_template = self.$profsel_container.find('> :first-child'),
		$profsels = [],
		profiles_byid = {};
	    for (var idx=0; idx < profiles.length; idx++) {
		    profiles_byid[profiles[idx].getProfileID()] = profiles[idx];
		    // also clone bound events!!!!
		var $profsel_el = $profsel_template.clone(true),
		    $profsel_a = $profsel_el
		    .find('> {0}'
			  .nformat(selectors.toggles_tab_has_catprof_id)
			 );
		var profsel_href = '#cat-{0}'.nformat(
		    selector_encode({cidp: profiles[idx].getIdpID(),
				     cprof: profiles[idx].getProfileID()})
		);
		(function($el) {
		    $.when(
			profiles[idx].getDisplay()
		    ).then(function(display) {
			if (!!display) {
			    $el.text(display);
			} else {
			    $el.html('&nbsp;');
			}
		    });
		}($profsel_a));
		$profsel_el.removeClass('active');
		$profsel_a.attr({'data-catprof': profiles[idx].getProfileID(),
				 'data-catidp': self.obj.id})
		    .data('_catprof', profiles[idx])
		    .attr('data-target',
			  selectors.target_catprofpane_with_cprof_id
			  .nformat({cprof: profiles[idx].getProfileID()})
			 )
		    .attr({'href': profsel_href,
			   'aria-controls': profsel_href.substr(1)});
		$profsels.push($profsel_el);
	    }
	    self.$profsel_container
		.html($profsels)
		.addClass('hidden');
	    return profiles_byid;
	},
	select_profile: function(profiles, profiles_byid) {
	    var self = this;
	    var state = hstate.fromFragment();
	    if (('cprof' in state) && (state.cprof in profiles_byid)) {
		$.publish(pubsubs.cprof.change.fromstate, [state]);
	    // } else if (!!_catProf && (_catProf.id in profiles_byid)) {
	    } else {
		for (var _idx = 0;
		     _idx < views.cprof.prev_stack.length &&
		     !(views.cprof.prev_stack[_idx] in profiles_byid);
		     _idx++); // empty statement
		if (_idx < views.cprof.prev_stack.length) {
		    $.publish(pubsubs.cprof.change.tostate,
			      [$.extend({}, state,
					{cprof: views.cprof.prev_stack[_idx],
					 _act: 'replace'})]);

		} else {
		    $.publish(pubsubs.cprof.change.tostate,
			      [$.extend({}, state,
					{cprof: profiles[0].getProfileID(),
					 _act: 'replace'})]);
		}
	    }
	},
	setup_title_icon: function(title, $icon) {
	    var self = views.cidp;
	    if (!!!title) {
		title = $(self.element).find('.title').text();
	    }
	    if (!!title) {
		var _title = exthandlers.modal_title.call(self.element, title);
		$(selectors.cat_modal)
		    .find(selectors.catui_institution)
		[(_title instanceof $) ? 'html' : 'text'](_title);
		if ($icon instanceof $) {
		    $icon.attr({title: title, alt: title});
		}
	    } else {
		$(selectors.cat_modal)
		    .find(selectors.catui_institution)
		    .html('&nbsp;');
	    }
	    $(selectors.cat_modal)
		.find(selectors.catui_container_logo)
		.html($icon)
	    [$icon === null ? 'addClass' : 'removeClass']('hidden');
	},
	appear: {
	    init: function() {
		var interval = 50;
		if (('appear_qinterval' in cuopts) &&
		    parseFloat(cuopts.appear_qinterval)) {
		    interval = parseFloat(cuopts.appear_qinterval);
		}
		this.queue = [];
		this.queueInterval = interval;
		this.getQueueDelay = function(queueLength, factor) {
		    factor = (typeof factor !== 'undefined') ?
			parseFloat(factor) : 1;
		    return (queueLength * this.queueInterval * factor)
			- (this.queueInterval * factor);
		}
	    },
	    elements: function() {
		return $(selectors.toggles_modal_has_cidp_id)
		    .get();
	    },
	    appear: function(el) {
		var self = views.cidp,
		    appear_self = this;
    		var $el = $(el),
    		    catIdpID = parseInt($el.data('catidp')),
		    _cidp = $el.data('_catidp');

		function lifo_queue_exec(q_when, q_then, delay_factor) {
    		    appear_self.queue.unshift(function() {
			$.when(q_when()).then(q_then, q_then);
		    });
		    setTimeout(function() {
			var qcb = appear_self.queue.shift();
			if (typeof qcb === 'function') {
			    qcb();
			}
		    }, appear_self.getQueueDelay(appear_self.queue.length, delay_factor));
		}

    		var cb2 = function(ret) {
    	    	    if (!Array.isArray(ret) ||
    	    		ret.length == 0) {
			$el.trigger(events.cidp_disable_selector);
    	    	    } else {
			$el.trigger(events.cidp_bind_selector);
		    }
    		}

		if (!!catIdpID && !!!_cidp) {
		    lifo_queue_exec(
			function() { return CAT.API.listProfiles(catIdpID); },
			cb2, 2
		    );
		}

		return this;
	    }
	},
	tou_cb: function(tou) {
	    var tou_url_start;
	    if (!!tou && (tou_url_start = tou.search(/(https?:)?\/\//)) != -1) {
		$(selectors.catui_cat_api_tou).attr('href', tou.substr(tou_url_start));
	    }
	},
	// static method
	bind_selectors: function(valid_cidp_byid) {
	    return $(selectors.toggles_modal_has_cidp_id).map(function() {
		var cidp = parseInt($(this).data('catidp'));
		if (!!!cidp || ((valid_cidp_byid instanceof Object) &&
				!(cidp in valid_cidp_byid))) {
		    return null; // excludes this from .map return val
		}
		$(this).trigger(events.cidp_bind_selector);
		return this;
	    });
	},
	// static method
	unbind_selectors: function(valid_cidp_byid) {
	    return $(selectors.toggles_modal_has_cidp_id).map(function() {
		if (valid_cidp_byid instanceof Object) {
		    var cidp = parseInt($(this).data('catidp'));
		    if (!!!cidp &&
			!(cidp in valid_cidp_byid)) {
			return null; //excludes this from .map return val
		    }
		}
		$(this).trigger(events.cidp_unbind_selector);
		return this;
	    });
	}
    }

    views.cprof = {
	handle: function(evt) {
	    var self = views.cprof;
	    switch (evt.type) {
	    case strip_namespace(events.click):
		evt.preventDefault();
		if ($(this).parent().hasClass('active')) {
		    return this;
		}
		var state = hstate.fromFragment(),
		    key = 'cprof',
		    val = $(this).attr('data-catprof');
		if (!(key in state) || state[key] !== val) {
		    state[key] = val;
		    return $.publish(pubsubs.cprof.change.tostate,
				     [state,
				      $(this)]);
		}
		break;
	    }
	    return this; // jQuery chaining
	},
	subscriber: function(evt, state, $el) {
	    var self = views.cprof;
	    switch (evt.type) {
	    case strip_namespace(pubsubs.cprof.remove.fromstate):
		break;
	    case strip_namespace(pubsubs.cprof.change.fromstate):
		if (!(state instanceof Object)) {
		    return false;
		}
		if ($el instanceof $) {
		    self.element = $el.get(0);
		} else {
		    $el = $(selectors.toggles_tab_with_cprof_id.nformat(state));
		    if ($el.length != 1) {
			return false;
		    }
		    self.element = $el.get(0);
		}
		self.main();
		break;
	    }
	    return this;
	},
	obj: undefined,
	prev_stack: [],
	prev_obj: {},
	main: function() {
	    var self = this;
	    var cprof = $(self.element).data('_catprof');
	    self.obj = (cprof instanceof catPrototypes.Profile) ?
		cprof :
		CAT.Profile(views.cidp.obj.id,
				    parseInt($(self.element).data('catprof')));

	    $(self.element).parent('li')
	    	.addClass('active')
	    	.siblings().removeClass('active');

	    self.setup_support();

	    self.setup_profpanes();
	},
	toggle_support_elements: function($supcon, hasSupport) {
	    var answer =     !!hasSupport ? 'yes' : 'no',
		answer_inv = !!hasSupport ? 'no' : 'yes',
		toggle =     { yes: 'addClass', no: 'removeClass' };
	    $supcon[toggle[answer_inv]]('hidden')
		.siblings().each(function() {
		    if ($(this).data('catui-support') === answer) {
			$(this)[toggle[!!hasSupport ? answer_inv : answer]]('hidden');
		    }
		    if ($(this).data('catui-support') === answer_inv) {
			$(this)[toggle[!!hasSupport ? answer : answer_inv]]('hidden');
		    }
		});
	},
	setup_support: function() {
	    var self = this;
	    $(selectors.catui_container_support)
		.addClass('hidden');
	    return $.when(
		self.obj.getLocalUrl(),
		self.obj.getLocalEmail(),
		self.obj.getLocalPhone()
	    ).then(self.setup_support_cb, self.setup_support_cb);
	},
	setup_support_cb: function(local_url, local_email, local_phone) {
	    var self = views.cprof,
		$support_container = $(selectors.catui_container_support_contact),
		$supportel_template = $support_container.find('> span:first-child'),
		$supportels = [];
	    if (!!!self.obj) {
		return null;
	    }
	    if (!!!local_url &&
		!!!local_email &&
		!!!local_phone) {
		self.toggle_support_elements($support_container, false);
	    } else {
		if (!!local_url) {
		    var $supportel = $supportel_template.clone(true),
			$supportel_i = $supportel.find('> i'),
			$supportel_a = $supportel.find('> a');
		    $supportel_i.attr('class', 'fa fa-link');
		    $supportel_a
			.attr('href',
			      (local_url.search(/(https?:)?\/\//) == 0) ?
			      local_url : '//' + local_url)
			.text(function() {
			    var txt = local_url.
				replace(/^((https?:)?\/\/)(www\.)?/, ''),
				lidx = txt.length - 1;
			    if (txt.indexOf('/') == lidx) {
				return txt.substr(0, lidx);
			    }
			    return txt;
			});
		    $supportels.push($supportel);
		}
		if (!!local_email) {
		    var $supportel = $supportel_template.clone(true),
			$supportel_i = $supportel.find('> i'),
			$supportel_a = $supportel.find('> a');
		    $supportel_i.attr('class', 'fa fa-envelope-o');
		    $supportel_a.attr('href', 'mailto:' + local_email)
			.text(local_email);
		    $supportels.push($supportel);
		}
		if (!!local_phone) {
		    var $supportel = $supportel_template.clone(true),
			$supportel_i = $supportel.find('> i'),
			$supportel_a = $supportel.find('> a');
		    $supportel_i.attr('class', 'fa fa-phone');
		    $supportel_a.attr('href', 'tel:' + local_phone)
			.text(local_phone);
		    $supportels.push($supportel);
		}
		$support_container.html($supportels);
		self.toggle_support_elements($support_container, true);
	    }
	    $(selectors.catui_container_support)
		.removeClass('hidden');
	    return this;
	},
	setup_profpanes: function() {
	    var self = this,
		deferreds = [];

	    var $profpane_container = $(selectors.cat_modal)
		.find(selectors.catui_profiles_container),
		$profpane_template = $profpane_container
		.find(selectors.catui_profile_container_template),
		$profpane_loading = $profpane_container
		.find(selectors.catui_profile_loading_placeholder),
		$profpane_error = $profpane_container
		.find(selectors.catui_profile_load_error);

	    $profpane_loading
	    	.addClass('active')
	    	.siblings().removeClass('active');

	    var $profpane = $profpane_container
		.find(selectors.catui_profile_container_with_catprofpane_id
		      .nformat({cprof: self.obj.getProfileID()}));
	    if ($profpane.length == 1) {
		self.$profpane = $profpane;
		self.activate_profpane();
		return $profpane;
	    }

	    $profpane = $profpane_template.clone(true);
	    $profpane
		.attr({'id': selector_encode({cidp: self.obj.getIdpID(),
					      cprof: self.obj.getProfileID()}),
		       'data-catui': 'profile-container',
		       'data-catui-panelrole': null,
		       'data-catprofpane': self.obj.getProfileID()});
	    self.$profpane = $profpane;

	    deferreds.push(
		$.when(
		    self.obj.getDescription()
		).then(self.setup_description_cb, self.setup_description_cb)
	    );

	    deferreds.push(
		$.when(
		    self.obj.getDevices()
		).then(self.setup_devicelist_cb, self.setup_devicelist_cb)
		    .then(self.setup_devicelist_cb2, self.setup_devicelist_cb2)
	    );

	    return $.when.apply($, deferreds)
		.then(
		    function() {
			$profpane_container
			    .append(self.$profpane);
			return self.activate_profpane();
		    },
		    function() {
			self.$profpane.remove();
			$profpane_error
	    		    .addClass('active')
	    		    .siblings().removeClass('active');
			return null;
		    }
		);
	},
	setup_description_cb: function(description) {
	    var self = views.cprof,
		$description_element = self.$profpane
		.find(selectors.catui_profile_description);

	    if (!!!self.obj) {
		// return null;
		return $.Deferred().reject(description);
	    }

	    if (!!description) {
		$description_element.text(description);
	    } else {
	    	$description_element.html('');
	    }
	    // if profiles <= 1 or profile title == description, hide description
	    if ($(selectors.catui_profile_select_container).children().length <= 1 ||
		$(self.element).text() == description ||
		!!!description) {
		$description_element.addClass('hidden');
	    } else {
		$description_element.removeClass('hidden');
	    }
	    return this;
	},
	setup_devicelist_cb: function(devices) {
	    var self = views.cprof;

	    if (!!!self.obj) {
		// return null;
		return $.Deferred().reject(devices);
	    }

	    if (!!devices) {
		return catPrototypes.Device.groupDevices(devices);
	    } else {
		return null;
	    }
	},
	setup_devicelist_cb2: function(grouped_devices) {
	    var self = views.cprof;

	    if (!!!self.obj) {
		//return null;
		return $.Deferred().reject(grouped_devices);
	    }

	    if (!!!grouped_devices) {
		return $.Deferred().reject(grouped_devices);
	    }
	    var $devicelist_container = self.$profpane
		.find(selectors.catui_devicelist_container),
		$devicegroup_heading_template = $devicelist_container
		.find('.panel-heading').first(),
		$devicegroup_template = $devicegroup_heading_template.next(),
		$device_template = $devicegroup_template
		.find('.list-group-item').first();
	    var devgroups = [],
		devgroup_id_from = $devicegroup_template.attr('id'),
		ungrouped_devices = {};
	    for (var devgroup in grouped_devices) {
		var $devgroup_heading = $devicegroup_heading_template.clone(true);
		var devgroup_id_to = devgroup_id_from
		    .nformat({cdev_group: devgroup});
		$devgroup_heading
		    .attr('id', function(idx, cur) {
			// return cur.nformat({cdev_group: devgroup});
			// return cur.replace(devgroup_id_from, devgroup_id_to);
			return '{0}_{1}'.nformat(
			    cur.replace(devgroup_id_from, devgroup_id_to),
			    self.$profpane.attr('id')
			);
		    })
		    .find('a')
		    .attr({ 'data-target': '#{0}_{1}'.nformat(devgroup_id_to,
							      self.$profpane.attr('id')),
			    'data-toggle': 'collapse-noanimation',
			    'aria-controls': '#{0}_{1}'.nformat(devgroup_id_to,
								self.$profpane.attr('id'))})
		    .text(devgroup);
		var $devgroup = $devicegroup_template.clone(true);
		$devgroup
		    .attr('id', '{0}_{1}'.nformat(devgroup_id_to,
						  self.$profpane.attr('id')))
		    .attr('aria-labelledby', function(idx, cur) {
			return cur.replace(devgroup_id_from,
					   '{0}_{1}'.nformat(
					       devgroup_id_to,
					       self.$profpane.attr('id'))
					  );
		    });
		var devs = [];
		for (var devidx = 0; devidx < grouped_devices[devgroup].length; devidx++) {
		    var $device = $device_template.clone(true),
			device_id = grouped_devices[devgroup][devidx].getDeviceID();
		    ungrouped_devices[device_id] = grouped_devices[devgroup][devidx];
		    $device.children('a')
			.data('_catdev', grouped_devices[devgroup][devidx])
			.attr('href',
			      '#cat-{0}'.nformat(
				  selector_encode({cidp: self.obj.getIdpID(),
						   cprof: self.obj.getProfileID(),
						   cdev: device_id}))
			     )
			.attr({'data-catdev': device_id,
			       'data-catprof': self.obj.getProfileID()});
		    $.when(
			grouped_devices[devgroup][devidx].getDisplay(),
			grouped_devices[devgroup][devidx].getDeviceCustomText()
		    ).then(function(display, custom_text) {
			var $a = $device.children('a');
			$a.text(display || device_id);
			if (!!custom_text) {
			    $a.append($('<small>').text(custom_text));
			}
		    });
		    devs.push($device);
		}
		$devgroup
		    .children('ul.list-group')
		    .empty()
		    .html(devs);
		devgroups.push($devgroup_heading, $devgroup);
	    }
	    $devicelist_container
		.find('.panel')
		.empty()
		.html(devgroups);
	    return this;
	},
	activate_profpane: function() {
	    var self = this;

	    self.$profpane
	    	.addClass('active')
	    	.siblings().removeClass('active');
	    $(selectors.catui_profile_select_container)
		.children()
		.each(function(idx, el) {
		    // by default hide profpane selector container
		    $(this).parent().addClass('hidden');
		    // but if there is more than one selector, show it and break
		    if (idx > 0) {
		    	$(this).parent().removeClass('hidden');
		    	return false;
		    }
		    return this;
		});

	    self.$profpane.find(selectors.catui_device_container)
		.siblings(selectors.catui_device_loading_placeholder).addClass('active')
		.siblings(':not(.active-exempt)').removeClass('active');

	    return self.select_cdev();
	},
	search_cdev: function(cdevid) {
	    var self = this;
	    return self.$profpane
		.find(selectors.changes_cdev_has_cdev_id_ctx_devicelist_container)
		.filter(function() {
		    return $(this).data('catdev') == cdevid;
		});
	},
	select_cdev: function() {
	    var self = this;
	    var state = hstate.fromFragment();
	    if (('cdev' in state) && self.search_cdev(state.cdev).length == 1) {
		$.publish(pubsubs.cdev.change.fromstate, [state]);
	    } else if (!!views.cdev.prev_obj &&
		       self.search_cdev(views.cdev.prev_obj.id).length == 1) {
		$.publish(pubsubs.cdev.change.tostate,
			  [$.extend({}, state,
				    {cdev: views.cdev.prev_obj.id,
				     _act: 'replace'}),
			  self.search_cdev(views.cdev.prev_obj.id)]);
	    } else if (self.search_cdev(cuopts.catDeviceGuess).length == 1) {
		$.publish(pubsubs.cdev.change.tostate,
			  [$.extend({}, state,
				    {cdev: cuopts.catDeviceGuess,
				     _act: 'replace'}),
			  self.search_cdev(cuopts.catDeviceGuess)]);
	    } else {
		self.$profpane
		    .find(selectors.catui_device_no_match)
		    .addClass('active')
		    .siblings()
		    .removeClass('active');
		return false;
	    }
	    return true;
	}
    }

    views.cdev = {
	handle: function(evt) {
	    var self = views.cdev;
	    switch (evt.type) {
	    case strip_namespace(events.click):
		evt.preventDefault();
		var state = hstate.fromFragment(),
		    key = 'cdev',
		    val = $(this).attr('data-catdev');
		if (!(key in state) || state[key] !== val) {
		    state[key] = val;
		    return $.publish(pubsubs.cdev.change.tostate,
				     [state,
				      $(this)]);
		}
		break;
	    }
	    return this; // jQuery chaining
	},
	subscriber: function(evt, state, $el) {
	    var self = views.cdev;
	    switch (evt.type) {
	    case strip_namespace(pubsubs.cdev.remove.fromstate):
		break;
	    case strip_namespace(pubsubs.cdev.change.fromstate):
		if (!(state instanceof Object)) {
		    return false;
		}
		if ($el instanceof $) {
		    self.element = $el.get(0);
		} else {
		    $el = $(selectors.changes_cdev_with_cprof_cdev_ids_ctx_catprofpane
			    .nformat(state));
		    if ($el.length != 1) {
			$(selectors.changes_cdev_nomatch_with_cprof_id
			  .nformat({cprof: state.cprof}))
		    	    .addClass('active')
		    	    .siblings()
		    	    .removeClass('active');
			return false;
		    }
		    self.element = $el.get(0);
		}
		self.main();
		break;
	    }
	    return this;
	},
	obj: undefined,
	prev_obj: undefined,
	main: function() {
	    var self = this;
	    var cdev = $(self.element).data('_catdev');
	    self.obj = (cdev instanceof catPrototypes.Device) ?
		cdev :
		CAT.Device(views.cidp.obj.id,
				   parseInt($(self.element).data('catprof')),
				   parseInt($(self.element).data('catdev')));

	    self.$device_container = $(self.element)
		.parents(selectors.catui_profile_container)
		.find(selectors.catui_device_container);

	    return self.setup_device();
	},
	setup_device: function() {
	    var self = this;

	    self.$device_container
		.siblings(selectors.catui_device_loading_placeholder).addClass('active')
		.siblings(':not(.active-exempt)').removeClass('active');
	    // HACK!
	    self.$device_container.closest(selectors.cat_modal).scrollTop(0);

	    return $.when(
		self.obj.getDeviceID(),
		self.obj.getDisplay(),
		self.obj.getStatus(),
		self.obj.getEapCustomText(),
		self.obj.getDeviceCustomText(),
		self.obj.getMessage(),
		self.obj.isRedirect(),
		self.obj.isSigned(),
		self.obj.getRedirect(),
		self.obj.cat.getLanguageDisplay(self.obj.lang)
	    ).then(self.setup_device_cb, self.setup_device_cb)
		.then(
		    function() {
			self.$device_container
			    .addClass('active')
			    .siblings(':not(.active-exempt)')
			    .removeClass('active');
			return true;
		    },
		    function() {
			console.warn('catdevchange master promise failed!', this, arguments);
			self.$device_container
			    .siblings(selectors.catui_device_load_error)
			    .addClass('active')
			    .siblings(':not(.active-exempt)')
			    .removeClass('active');
			return false;
		    });
	},
	set_device_field: function(data_catui_val, text) {
	    var self = this,
		$el = self.$device_container
		.find('[data-catui="{0}"]'
		      .nformat(data_catui_val));
	    if (!!text) {
		if (typeof text === 'string') {
		    $el.removeClass('hidden').text(text);
		} else if (typeof text === 'function') {
		    $el.removeClass('hidden').each(text);
		}
	    } else {
		$el.addClass('hidden').empty();
	    }
	    return $el;
	},
	setup_device_cb: function(device_id,
				  device_display,
				  device_status,
				  device_eapcustomtext,
				  device_devicecustomtext,
				  device_message,
				  device_isredirect,
				  device_issigned,
				  device_redirect,
				  device_lang_display) {
	    var self = views.cdev;

	    if (!!!self.obj) {
		// return null;
		return $.Deferred().reject(null);
	    }

	    self.set_device_field('device-display', device_display || device_id);
	    self.set_device_field('device-eapcustomtext', device_eapcustomtext);
	    self.set_device_field('device-devicecustomtext', device_devicecustomtext);
	    self.set_device_field('device-message',
				  !!device_message ?
				  function() {
				      $(this).find('[role="message"]')
					  .html(device_message)
					  .find('a').each(function() {
					      var href = $(this).attr('href'),
						  href_slash_idx = href.indexOf('/');
					      if (href_slash_idx <= 0 &&
						  href.search('//') != 0) {
						  $(this).attr('href',
							       self.obj.cat.localDownloadBase() +
							       href.substr(href_slash_idx + 1));
					      }
					      return this;
					  });
				      $(this)
					  .removeClass('catui-message-acknowledged');
				      return this;
				  } :
				  function() {
				      $(this).addClass('hidden')
					  .removeClass('catui-message-acknowledged');
				      return this;
				  });
	    self.set_device_field('device-redirectmessage',
				  device_isredirect ?
				  function() {
				      var device_redirect_url =
					  (device_redirect.search(/(https?:)?\/\//) == 0) ?
					  device_redirect : '//' + device_redirect;
				      $(this)
					  .find(
					      'a{0}'.nformat(
						  selectors.catui_device_redirecturl)
					  )
					  .attr('href', device_redirect_url)
					  .text(device_redirect);
				      return this;
				  } :
				  function() {
				      $(this)
					  .addClass('hidden')
					  .find(
					      'a{0}'.nformat(
						  selectors.catui_device_redirecturl)
					  )
					  .attr('href', null)
					  .text(null);
				      return this;
				  });
	    self.set_device_field('device-signed',
				  function() {
				      var act = !device_issigned ? 'addClass' : 'removeClass';
				      $(this)[act]('hidden');
				      return this;
				  });
	    self.set_device_field('device-language',
				  function() {
				      var act = !!!device_lang_display ? 'addClass' : 'removeClass';
				      $(this)
					  .text(device_lang_display || '')
					  .parent('span')[act]('hidden');
				      return this;
				  });
	    if (!device_isredirect) {
		self.set_device_field('device-download',
				      function() {
					  $(this)
					      .removeClass('download-failed')
					      .find('button')
					      .removeClass('btn-danger')
					      .addClass('btn-success')
					      .data('_catdev', self.obj)
					      .find(selectors.catui_dltxt_init)
					      .removeClass('hidden')
					      .siblings().addClass('hidden');
				      });
	    }
	    return $.when(
		self.obj.getDeviceInfo()
	    ).then(self.setup_deviceinfo_cb, self.setup_deviceinfo_cb);
	},
	setup_deviceinfo_cb: function(device_deviceinfo) {
	    var self = views.cdev;

	    if (!!!self.obj) {
		// return null;
		return $.Deferred().reject(device_deviceinfo);
	    }

	    if (!!!device_deviceinfo) {
		self.set_device_field('device-deviceinfo', function() {
		    $(this)
			.addClass('hidden')
			.find('.panel-body')
			.empty();
		});
		// don't reject as e.g. redirect devices will not have deviceinfo
		// return $.Deferred().reject(null);
		return false;
	    }
	    self.set_device_field('device-deviceinfo', function() {
		var devinfo_id = 'deviceinfo_{0}_{1}'
		    .nformat(
			$(this)
			    .closest(selectors.catui_profile_container)
			    .attr('id'),
			self.obj.id);
		$(this)
		    .removeClass('hidden')
		    .find('.panel-heading')
		      .attr('id', 'heading_' + devinfo_id)
		      .find('a')
		        .attr({'data-target': '#' + devinfo_id,
			       'aria-controls': devinfo_id})
		        .end()
		      .end()
		    .find('[role="tabpanel"]')
		    .attr({'id': devinfo_id,
			   'aria-labelledby': 'heading_' + devinfo_id})
		    .find('.panel-body')
		      .html(device_deviceinfo)
		      .find('a').each(function() {
			  var href = $(this).attr('href');
			  if (href.search(/(https?:)?\/\//) != 0) {
			      href = '//' + href;
			      $(this).attr('href', href);
			  }
			  return this;
		      });
		return this;
	    });
	    return device_deviceinfo;
	},
	// click handler, may also be called with button as 1st arg or without args
	handle_download: function(evt) {
	    var self = views.cdev,
		$el = evt,
		clickhandler = false;
	    if ((evt instanceof $.Event)
		&& evt.type == strip_namespace(events.click)) {
		evt.preventDefault();
		self.$download_button = $(this);
		clickhandler = true;
	    } else if (($el instanceof $) && $el.length == 1) {
		self.$download_button = $el;
	    } else {
		self.$download_button = self.$device_container
		    .find(selectors.catui_device_download);
	    }
	    if (self.$download_button.length != 1) {
		return false;
	    }
	    var device = self.$download_button.data('_catdev') || self.obj;
	    if (!(device instanceof catPrototypes.Device)) {
		console.warn('aborting! device is not a CAT.Device', device);
		return false;
	    }
	    self.$download_button
		.find(selectors.catui_dltxt_generate)
		.removeClass('hidden')
		.siblings().addClass('hidden');
	    device.getDownload()
		.then(self.handle_download_cb,
		      self.handle_download_cb);
	    if (clickhandler) {
		return this;
	    }
	},
	handle_download_cb: function(dlurl) {
	    var self = views.cdev;
	    if (dlurl !== null) {
		self.$download_button
		    .find(selectors.catui_dltxt_download)
		    .removeClass('hidden')
		    .siblings().addClass('hidden');
	    } else {
		self.$download_button
		    .removeClass('btn-success').addClass('btn-danger')
		    .find(selectors.catui_dltxt_fail)
		      .removeClass('hidden')
		      .siblings().addClass('hidden')
		    .end()
		    .closest(selectors.catui_device_download)
		    .addClass('download-failed');
		return $.Deferred().reject(dlurl);
	    }
	    return dlurl;
	},
	// click handler, may also be called with button as 1st arg or without args
	ack_redirect: function(evt) {
	    var self = views.cdev,
		$el = evt,
		$target,
		clickhandler = false;
	    if ((evt instanceof $.Event)
		&& evt.type == strip_namespace(events.click)) {
		evt.preventDefault();
		$target = $(this)
		    .closest(selectors.catui_device_redirectmessage)
		    .find(selectors.catui_device_redirecturl);
		clickhandler = true;
	    } else if (($el instanceof $) && $el.length == 1) {
		$target = $el
		    .closest(selectors.catui_device_redirectmessage)
		    .find(selectors.catui_device_redirecturl);
	    } else {
		$target = self.$device_container
		    .find(selectors.catui_device_redirectmessage)
		    .find(selectors.catui_device_redirecturl);
	    }
	    if ($target.length == 1 &&
		(clickhandler ? evt.target !== $target.get(0) : true)) {
		var href = $target.attr('href'),
		    target = $target.attr('target');
		if (href) {
		    if (target == '_blank') {
			root.open(href);
		    } else {
			root.location.href = href;
		    }
		    if (clickhandler) {
			return this;
		    }
		} else {
		    return false;
		}
	    } else {
		return false;
	    }
	},
	// click handler, may also be called with button as 1st arg or without args
	ack_device_msg: function(evt) {
	    var self = views.cdev,
		$el = evt,
		$target,
		clickhandler = false;
	    if ((evt instanceof $.Event)
		&& evt.type == strip_namespace(events.click)) {
		evt.preventDefault();
		$target = $(this).closest(selectors.catui_device_message);
		clickhandler = true;
	    } else if (($el instanceof $) && $el.length == 1) {
		$target = $el.closest(selectors.catui_device_message);
	    } else {
		$target = self.$device_container
		    .find(selectors.catui_device_message);
	    }
	    if ($target.length == 1) {
		$target.addClass('catui-message-acknowledged');
		if (clickhandler) {
		    return this;
		}
	    } else {
		return false;
	    }
	}
    }


    function setup_subscribers(act) {
	act = act ? 'subscribe' : 'unsubscribe';
	$[act](pubsubs.cidp.change.fromstate, views.cidp.subscriber);
	$[act](pubsubs.cidp.remove.fromstate, views.cidp.subscriber);
	$[act](pubsubs.cprof.change.fromstate, views.cprof.subscriber);
	$[act](pubsubs.cprof.remove.fromstate, views.cprof.subscriber);
	$[act](pubsubs.cdev.change.fromstate, views.cdev.subscriber);
	$[act](pubsubs.cdev.remove.fromstate, views.cdev.subscriber);
	(function act_recursive(obj, act, stopic, subscriber) {
	    for (var k in obj) {
		if (obj[k] instanceof Object) {
		    act_recursive(obj[k], act, stopic, subscriber);
		} else if (k == stopic) {
		    $[act](obj[k], subscriber);
		}
	    }
	}(pubsubs, act, 'tostate', controllers.tostate));
    }
    function setup_handlers(act) {
	act = act ? 'on' : 'off';
	$(root)[act](events.history_change, controllers.fromstate);
	$(document)
	    [act](events.click,
		selectors.toggles_collapse_noanimation,
		handlers.bs_collapsible_noanimation)
	    [act](events.click,
		'{0}, {1}, {2}'.nformat(
		    '{0} .panel-heading'.nformat(selectors.catui_devicelist_container),
		    '{0} .panel-heading'.nformat(selectors.catui_device_deviceinfo),
		    '{0} .list-group-item'.nformat(selectors.catui_devicelist_container)
		),
		handlers.bs_collapsible_click_propagate)
	    [act](events.click,
		'{0} {1}'.nformat(
		    selectors.catui_devicelist_container,
		    selectors.toggles_collapse_noanimation
		),
		handlers.bs_collapsible_hide_other);
	$(selectors.inst_list_ul)
	    [act]('mouseup mousedown focusin', handlers.composite_click_optimized);
	$(selectors.cat_modal)
	[act]('hidden.bs.modal', handlers.bs_modal_hidden);

	$(selectors.toggles_modal_has_cidp_id)
	    [act](events.cidp_bind_selector, views.cidp.handle)
	    [act](events.cidp_unbind_selector, views.cidp.handle)
	    [act](events.cidp_disable_selector, views.cidp.handle);
	$(selectors.toggles_tab_has_catprof_id)
	    [act](events.click, views.cprof.handle);
	$(selectors.changes_cdev_has_cdev_id_ctx_devicelist_container)
	    [act](events.click, views.cdev.handle);
	$('{0} button'.nformat(selectors.catui_device_download))
	    [act](events.click, views.cdev.handle_download);
	$('{0} button'.nformat(selectors.catui_device_redirectmessage))
	    [act](events.click, views.cdev.ack_redirect);
	$('{0} button'.nformat(selectors.catui_device_message))
    	    [act](events.click, views.cdev.ack_device_msg);
    }


    return function(_cuopts, overrides) {
	var on = true,
	    off = false,
	    init_d = $.Deferred(),
	    _appear,
	    overridable = ['selectors', 'events', 'pubsubs', 'exthandlers',
			   'handlers', 'views', 'controllers'];

	if (_cuopts instanceof Object) {
	    $.extend(true, cuopts, _cuopts);
	}
	if (!('CAT' in cuopts)) {
	    // throw something?
	    return null;
	} else {
	    CAT = cuopts.CAT;
	    (function() {
		for (var o, k = 0; k < arguments.length; k++) {
		    o = arguments[k];
		    catPrototypes[o] = CAT[o]().constructor;
		}
	    }('IdentityProvider', 'Profile', 'Device'));
	}
	if (!('catDeviceGuess' in cuopts)) {
	    cuopts.catDeviceGuess =
		catPrototypes.Device.guessDeviceID(navigator.userAgent);
	}

	if (overrides instanceof Object) {
	    (function(overrides, overridable) {
		for (var ov in overrides) {
		    for (var i=0;
			 i < overridable.length &&
			 ov != overridable[i];
			 i++); // empty statement
		    if (i < overridable.length &&
			(overrides[ov] instanceof Object) &&
			(eval(ov) instanceof Object)) {
			$.extend(true, eval(ov), overrides[ov]);
		    }
		}
	    }(overrides, overridable));
	}

	var init_ret = {
	    opts: cuopts,
	    selectors: selectors,
	    events: events,
	    pubsubs: pubsubs,
	    handlers: handlers,
	    exthandlers: exthandlers,
	    views: views,
	    controllers: controllers,
	    initialized: init_d,
	    appear: _appear,
	    teardown: function() {
		if ((this.appear instanceof Object) &&
		    typeof this.appear.destroy === 'function') {
		    this.appear.destroy();
		    delete this.appear;
		}
		views.cidp.unbind_selectors();
		setup_subscribers(off);
		setup_handlers(off);
		CAT.API.touCallBack($.noop);
	    }
	}

	function init_cb(ret) {
	    if (!(ret instanceof Object)) {
		return init_d.reject();
	    }
	    var cidp_selectors = views.cidp.bind_selectors(ret);
	    if (cidp_selectors.length == 0) {
		return init_d.reject();
	    }
	}

	function init_success() {
	    if (('appear' in root) &&
		typeof root.appear === 'function') {
		init_ret.appear = root.appear(views.cidp.appear);
	    } else {
		views.cidp.appear.init();
		$(selectors.toggles_modal_has_cidp_id).each(function() {
		    if (!!!$(this).data('_cidp')) {
			views.cidp.appear.appear(this);
		    }
		    return this;
		});
	    }
	    init_d.resolve();
	}

	function init_fail() {
	    init_ret.teardown();
	    init_d.reject();
	}

	setup_subscribers(on);
	setup_handlers(on);
	CAT.API.touCallBack(views.cidp.tou_cb);

	$.when(
	    CAT.API.listAllIdentityProvidersByID()
	).then(init_cb, init_cb)
	    .then(init_success, init_fail);

	setTimeout(function() {
	    hstate.init();
	    var wlh = root.location.hash;
	    if (wlh.search(/#cat[-=]/) == 0) {
		var dec_wlh = selector_decode(wlh.substr(5));
		hstate.toFragment(dec_wlh, 'replace', true);
	    } else {
		$(root).trigger(events.history_change);
	    }
	});

	return init_ret;
    }
}));
