;

(function($){

    if (!String.prototype.naive_format) {
	String.prototype.naive_format = function() {
	    var args = Array.from_arguments.apply(null, arguments),
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
    }

    var btoa = window.btoa || $.base64.btoa,
	atob = window.atob || $.base64.atob;
    function selector_encode(obj) {
	return btoa(JSON.stringify(obj)).replace(/=/g, '_');
    }
    function selector_decode(hash) {
	return JSON.parse(atob(hash.replace(/_/g, '=')));
    }

    function hashAct(key, val, hard) {
	var state = $.fn.HashHandle('hash'),
	    hard = !!hard && 'Hard' || '';
	if (key in state) {
	    if (state[key] == val || typeof val === 'undefined') {
		$.fn.HashHandle('remove' + hard, key);
	    } else {
		$.fn.HashHandle('add' + hard, key, val);
	    }
	} else if (typeof val !== 'undefined') {
	    $.fn.HashHandle('add' + hard, key, val);
	}
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
    },
	events = {
	    history_change: 'onpopstate' in window ? 'popstate' : 'hashchange',
	    logosup_hide: 'hide.logosup.cat',
	    logosup_show: 'show.logosup.cat',
	    click_composite: 'compositeClick',
	    disable_noprofiles: 'disableNoProfiles',
	    change_cidp: 'catIdpChange',
	    change_cprof: 'catProfChange',
	    change_cdev: 'catDevChange',
	}

    var catIdp,
	catProf, _catProf = [], _catProfO = {},
	catDev, _catDev;

    $(window).on(events.history_change, function (evt) {
	var state = $.fn.HashHandle("hash"),
	    pairs = {
		cidp:  { evt: events.change_cidp,  obj: catIdp  },
		cprof: { evt: events.change_cprof, obj: catProf },
		cdev:  { evt: events.change_cdev,  obj: catDev  }
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
	    // console.log(key +' stateChange: '+ stateChange);
	    if (stateChange === 0) {
		continue;
	    }
	    switch (key) {
	    case 'cidp':
		if (stateChange === 2) {
		    catIdp = undefined;
		    $('{0}.in'.naive_format(selectors.cat_modal)).modal('hide');
		} else {
		    return $(selectors.toggles_modal_with_cidp_id
			     .naive_format({cidp: state[key]}))
			.triggerHandler(pairs[key].evt);
		}
		// fallthrough if stateChange === 2
	    case 'cprof':
		if (stateChange === 2) {
		    if (key != 'cprof') {
			// don't blindly set _catProf (last catProf), but push
			// catProf.id in front of _catProf and add catProf to
			// _catProfO
			if (!!catProf) {
			    var idx;
			    if ((idx = _catProf.indexOf(catProf.id)) != -1) {
				_catProf.splice(idx, 1);
			    } else {
				_catProfO[catProf.id] = catProf;
			    }
			    _catProf.unshift(catProf.id);
			}
			hashAct('cprof', undefined, true);
		    }
		    catProf = undefined;
		} else {
		    return $(selectors.toggles_tab_with_cprof_id
			     .naive_format({cprof: state[key]}))
			.triggerHandler(pairs[key].evt);
		}
		// fallthrough if stateChange === 2
	    case 'cdev':
		if (stateChange === 2) {
		    if (key != 'cdev') {
			_catDev = !!catDev && catDev || _catDev;
			hashAct('cdev', undefined, true);
		    }
		    catDev = undefined;
		} else {
		    if (!('cprof' in state)) {
			console.log('have cdev but no cprof!!');
			break;
		    }
		    var $catdev_trigger_el =
			$(selectors.changes_cdev_with_cprof_cdev_ids_ctx_catprofpane
			  .naive_format({cprof: state.cprof,
					 cdev: state[key]}));
		    if ($catdev_trigger_el.length == 1) {
		    	$catdev_trigger_el.triggerHandler(pairs[key].evt);
		    } else {
			$(selectors.changes_cdev_nomatch_with_cprof_id
			  .naive_format({cprof: state.cprof}))
			    .addClass('active')
			    .siblings()
			    .removeClass('active');
		    }
		}
		break;
	    }
	}
	return this;
    });

    setTimeout(function() {
	var wlh = window.location.hash;
	if (wlh.search(/#cat[-=]/) == 0) {
	    var dec_wlh = selector_decode(wlh.substr(5));
	    $.fn.HashHandle('_goHard', dec_wlh);
	} else {
	    $(window).trigger(events.history_change);
	}
    });

    // light-weight bootstrap collapsible without animation
    $(document)
	.on('click',
	    selectors.toggles_collapse_noanimation,
	    function(evt) {
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
	    });	    
    // usability enhancement for accordion collapsibles (without animation)
    // propagate clicks to the device group/device info headings, device selectors
    // from their container elements
    $(document)
	.on('click',
	    '{0}, {1}, {2}'.naive_format(
		'{0} .panel-heading'.naive_format(selectors.catui_devicelist_container),
		'{0} .panel-heading'.naive_format(selectors.catui_device_deviceinfo),
		'{0} .list-group-item'.naive_format(selectors.catui_devicelist_container)
	    ),
	    function (evt) {
		var $that = $(this)
		    .find('{0},{1}'.naive_format(
			selectors.toggles_collapse_noanimation,
			selectors.changes_cdev_has_cdev_id)
			 );
		if ($that.length > 0 &&
		    evt.target !== $that.get(0) &&
		    $that.find(evt.target).length == 0) {
		    return $that.trigger('click');
		}
		return this;
	    });
    // hiding other device groups upon device group selection
    // workaround for collapse data-parent not working
    $(document)
	.on('click',
	    '{0} {1}'.naive_format(
		selectors.catui_devicelist_container,
		selectors.toggles_collapse_noanimation
	    ),
	    function (evt) {
	    $(this)
		.parent('.panel-heading')
		.siblings($(this).data('target'))
		.siblings('.panel-collapse.in')
		.removeClass('in');
	    return this;
	});


    $('{0},{1}'.naive_format(selectors.catui_container_logo,
			     selectors.catui_container_support))
	.on(events.logosup_hide, function (evt) {
	    $(this).addClass('hidden');
	    return this;
	})
	.on(events.logosup_show, function (evt) {
	    $(this).removeClass('hidden');
	    return this;
	});

    // buttons move around as they grow bigger in focus state
    // click may fire on a different element or not at all
    // thus we trigger a "composite click" on the element where mousedown fired
    // implicitly this means releasing mouse outside the original button (but still inside
    // ul.insts) will still fire click -- which is what we usually want
    // this seems to work fine with touch clicks, but needs more testing
    // ref:
    // https://bugzilla.mozilla.org/show_bug.cgi?id=326851
    $(selectors.inst_list_ul)
    	.on('mouseup mousedown focusin', function (evt) {
	    // only react on "left-click"
	    if (evt.type != 'focusin' && evt.which != 1) {
		return this;
	    }
	    var buttonPressed = evt.type == 'mouseup' ? $(this).data('_buttonpressed') :
		$(evt.target).closest(selectors.toggles_modal_has_cidp_id);
	    switch (evt.type) {
	    case 'mouseup':
		if (buttonPressed instanceof $) {
		    buttonPressed.trigger(events.click_composite);
		    $(this).removeData('_buttonpressed');
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
	});

    $(selectors.cat_modal).on('hidden.bs.modal', function(evt) {
	var state = $.fn.HashHandle('hash'),
	    cidp;
	if ('cidp' in state) {
	    cidp = state.cidp;
	    // hashHandle remove cidp
	    hashAct('cidp');
	}
	if (typeof(cidp) !== 'undefined') {
	    $(selectors.toggles_modal_with_cidp_id
	      .naive_format({cidp: cidp}))
		.focus();
	}
	return this;
    });

    $(selectors.toggles_modal_has_cidp_id)
	.on(events.click_composite, function (evt) {
	    // evt.preventDefault();
	    var key = 'cidp',
		val = $(this).attr('data-catidp');
	    hashAct(key, val);
	    return this;
	})
	.on(events.disable_noprofiles, function (evt) {
	    evt.preventDefault();
	    var href = $(this).data('idu');
	    $(this)
		.attr({
		    'data-target': null,
		    'data-toggle': null,
		    'href': href,
		    'data-idu': null,
		    'data-catidp': null
		})
		.removeData('target toggle catidp idu').off(events.click_composite);
	    return this;
	})
	.on(events.change_cidp, test_change_cidp);

    function test_change_cidp(evt) {
	    var button = this;
	    $('{0},{1}'.naive_format(selectors.catui_container_logo,
				     selectors.catui_container_support))
		.triggerHandler(events.logosup_hide);
	    catIdp = $(button).data('_catidp');
	    if (!(catIdp instanceof CAT.IdentityProvider().constructor)) {
		catIdp = CAT.IdentityProvider(parseInt($(button).data('catidp')));
		$(button).data('_catidp', catIdp);
	    }
	    // var cb_profiles = function(profiles)
	    var cb = function(title, $icon, profiles) {
		// console.log('catIdpChange cb:', arguments);
		if (profiles === null ||
		    !(profiles instanceof Array) ||
		    profiles.length == 0) {
		    $(button).triggerHandler(events.disable_noprofiles);
		    // avoid async catIdp.getEntityID() for now
		    // hashhandle removeHard cidp
		    hashAct('cidp', catIdp.id, true);
		    // hashAct('cidp', undefined, true);
		    if (!!NProgress) {
			NProgress.done();
		    }
		    return this;
		}
		var $profsel_container = $(selectors.cat_modal)
		    .find(selectors.catui_profile_select_container),
		    $profsel_template = $profsel_container.find('> :first-child');
		var $profsels = [];
		var profiles_byid = {};
		for (var idx=0; idx < profiles.length; idx++) {
		    profiles_byid[profiles[idx].getProfileID()] = profiles[idx];
		    // console.log("profile:", idx, profiles[idx]);
		    // also clone bound events!!!!
		    var $profsel_el = $profsel_template.clone(true),
			$profsel_a = $profsel_el.find('> {0}'.naive_format(
			    selectors.toggles_tab_has_catprof_id));
		    // $profsel_el[(idx == 0) ? 'addClass' : 'removeClass']('active');
		    $.when(
			profiles[idx].getDisplay()
		    ).then(function(display) {
			if (!!display) {
			    $profsel_a.text(display);
			} else {
			    $profsel_a.html('&nbsp;');
			}
		    });
		    $profsel_el.removeClass('active');
		    $profsel_a.attr('data-catprof', profiles[idx].getProfileID())
			.data('_catprof', profiles[idx])
			.attr('data-target',
			      selectors.target_catprofpane_with_cprof_id
			      .naive_format({cprof: profiles[idx].getProfileID()})
			     )
			.attr('href',
			      '#cat-{0}'.naive_format(
				  selector_encode({cidp: profiles[idx].getIdpID(),
						   cprof: profiles[idx].getProfileID()})
			      )
			     );
		    $profsels.push($profsel_el);
		}
		$profsel_container
		    .html($profsels)
		    .addClass('hidden');

		var state = $.fn.HashHandle("hash");
		if (('cprof' in state) && (state.cprof in profiles_byid)) {
		    $profsel_container
			.find(
			    selectors.toggles_tab_with_cprof_id
				.naive_format({cprof: state.cprof})
			)
			.triggerHandler(events.change_cprof);
		// } else if (!!_catProf && (_catProf.id in profiles_byid)) {
		} else {
		    for (var _idx = 0;
			 _idx < _catProf.length && !(_catProf[_idx] in profiles_byid);
			 _idx++); // empty statement
		    if (_idx < _catProf.length) {
			$profsel_container
			    .find(
				selectors.toggles_tab_with_cprof_id
				    .naive_format({cprof: _catProf[_idx]})
			    )
		    	    .data('_catprof', _catProfO[_catProf[_idx]]);
			hashAct('cprof', _catProf[_idx], true);
		    } else {
			hashAct('cprof', profiles[0].getProfileID(), true);
		    }
		}

		if (!!!title) {
		    title = $(button).find('.title').text();
		}
		if (!!title) {
		    if ($(button).data('idu')) {
			var title_a = $('<a>');
			title_a.attr('href', $(button).data('idu'))
			    .text(title)
			    .append($(button).children('i').clone());
			$(selectors.cat_modal)
			    .find(selectors.catui_institution)
			    .html(title_a);
		    } else {
			$(selectors.cat_modal)
			    .find(selectors.catui_institution)
			    .text(title);
		    }
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
		    .triggerHandler(
			$icon !== null ? events.logosup_show : events.logosup_hide
		    );

		if (!!NProgress) {
		    NProgress.done();
		}

		$(selectors.cat_modal)
		    .modal('show');

		return this;
	    }

	    if (!!NProgress) {
		NProgress.start();
	    }
	    return $.when(
		catIdp.getDisplay(),
		catIdp.getIcon(),
		catIdp.getProfiles(true)
	    ).then(cb, cb);	    
    }


    $(selectors.toggles_tab_has_catprof_id)
	.on('click', function (evt) {
	    evt.preventDefault();
	    if ($(this).parent().hasClass('active')) {
		return this;
	    }
	    var key = 'cprof',
		val = $(this).attr('data-catprof');
	    hashAct(key, val);
	    return this;
	})
	.on(events.change_cprof, test_change_cprof);

    function test_change_cprof(evt) {
 	    var button = this,
		profile = $(button).data('_catprof');
	    catProf = (profile instanceof CAT.Profile().constructor) ?
		profile : CAT.Profile(catIdp.id,
	    			      parseInt($(button).data('catprof')));
	    var deferreds_catprofchange = [];

	    $(button).parent('li')
	    	.addClass('active')
	    	.siblings().removeClass('active');

	    $(selectors.catui_container_support)
		.triggerHandler(events.logosup_hide);
	    var $support_container = $(selectors.catui_container_support_contact),
		$supportel_template = $support_container.find('> span:first-child');
	    var cb_support = function(local_url, local_email, local_phone) {
		function toggleSupportElements($supcon, hasSupport) {
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
		}
		if (!!!local_url &&
		    !!!local_email &&
		    !!!local_phone) {
		    toggleSupportElements($support_container, false);
		    $(selectors.catui_container_support)
			.triggerHandler(events.logosup_show);
		    return this;
		} else {
		    $supportels = [];
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
		    toggleSupportElements($support_container, true);
		    $(selectors.catui_container_support)
			.triggerHandler(events.logosup_show);
		    return this;
		}
	    }
	    $.when(
		catProf.getLocalUrl(),
		catProf.getLocalEmail(),
		catProf.getLocalPhone()
	    ).then(cb_support, cb_support);

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
		      .naive_format({cprof: catProf.getProfileID()}));
	    if ($profpane.length == 1) {
		// console.log('found profpane!');
		$profpane
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

		$profpane.find(selectors.catui_device_container)
		    .siblings(selectors.catui_device_loading_placeholder).addClass('active')
		    .siblings(':not(.active-exempt)').removeClass('active');

		var state = $.fn.HashHandle("hash"),
		    cdev_search = function(cdevid) {
			return $profpane
			    .find(selectors.changes_cdev_has_cdev_id_ctx_devicelist_container)
			    .filter(function() { return $(this).data('catdev') == cdevid; });
		    }
		if (('cdev' in state) && cdev_search(state.cdev).length == 1) {
		    $profpane
			.find(selectors.changes_cdev_with_cdev_id
			      .naive_format({cdev: state.cdev}))
			.triggerHandler(events.change_cdev);
		} else if (!!_catDev && cdev_search(_catDev.id).length == 1) {
		    hashAct('cdev', _catDev.id, true);
		} else if (cdev_search(catDeviceGuess).length == 1) {
		    hashAct('cdev', catDeviceGuess, true);
		} else {
		    $profpane
			.find(selectors.catui_device_no_match)
			.addClass('active')
			.siblings()
			.removeClass('active');
		}

		return this;
	    }
	    $profpane = $profpane_template.clone(true);
	    $profpane
		.attr({'id': selector_encode({cidp: catProf.getIdpID(),
					      cprof: catProf.getProfileID()}),
		       'data-catui': 'profile-container',
		       'data-catprofpane': catProf.getProfileID()});

	    var cb_description = function(description) {
		var $description_element = $profpane
		    .find(selectors.catui_profile_description);
		if (!!description) {
		    $description_element.text(description);
		} else {
		    $description_element.html('');
		}
		// if profiles <= 1 or profile title == description, hide description
		if ($(selectors.catui_profile_select_container).children().length <= 1 ||
		    $(button).text() == description ||
		    !!!description) {
		    $description_element.addClass('hidden');
		} else {
		    $description_element.removeClass('hidden');
		}
	    }
	    deferreds_catprofchange.push(
		$.when(
		    catProf.getDescription()
		).then(cb_description, cb_description)
	    );

	    var cb_devicelist = function(devices) {
		if (!!devices) {
		    return CAT.Device().constructor.groupDevices(devices);
		} else {
		    return null;
		}
	    }
	    var cb_devicelist_final = function(grouped_devices) {
		// console.log('cb2:', grouped_devices);
		// console.log('cb2 $profpane.selector:', $profpane);
		if (!!!grouped_devices) {
		    var d = new $.Deferred();
		    d.reject(grouped_devices);
		    return d.promise();
		}
		var $devicelist_container = $profpane.find(selectors.catui_devicelist_container),
		    $devicegroup_heading_template = $devicelist_container.find('.panel-heading'),
		    $devicegroup_template = $devicegroup_heading_template.next(),
		    $device_template = $devicegroup_template.find('.list-group-item').first();
		var devgroups = [],
		    devgroup_id_from = $devicegroup_template.attr('id'),
		    ungrouped_devices = {};
		for (var devgroup in grouped_devices) {
		    var $devgroup_heading = $devicegroup_heading_template.clone(true);
		    var devgroup_id_to = devgroup_id_from
			.naive_format({cdev_group: devgroup});
		    $devgroup_heading
			.attr('id', function(idx, cur) {
			    return cur.naive_format({cdev_group: devgroup});
			    // return cur.replace(devgroup_id_from, devgroup_id_to);
			})
			.find('a')
			.attr({ 'data-target': '#{0}_{1}'.naive_format(devgroup_id_to,
								       $profpane.attr('id')),
				'data-toggle': 'collapse-noanimation',
				'aria-controls': '#{0}_{1}'.naive_format(devgroup_id_to,
									 $profpane.attr('id'))})
			.text(devgroup);
		    var $devgroup = $devicegroup_template.clone(true);
		    $devgroup
			.attr('id', '{0}_{1}'.naive_format(devgroup_id_to,
							   $profpane.attr('id')))
			.attr('aria-labelledby', function(idx, cur) {
			    return cur.replace(devgroup_id_from,
					       '{0}_{1}'.naive_format(
						   devgroup_id_to,
						   $profpane.attr('id'))
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
				  '#cat-{0}'.naive_format(
				      selector_encode({cidp: catProf.getIdpID(),
						       cprof: catProf.getProfileID(),
						       cdev: device_id}))
				 )
			    .attr({'data-catdev': device_id,
				   'data-catprof': catProf.getProfileID()});
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
			.children('ul')
			.html(devs);
		    devgroups.push($devgroup_heading, $devgroup);
		}
		$devicelist_container
		    .find('.panel')
		    .html(devgroups);
	    }
	    deferreds_catprofchange.push(
		$.when(
		    catProf.getDevices()
		).then(cb_devicelist, cb_devicelist)
		    .then(cb_devicelist_final, cb_devicelist_final)
	    );

	    $.when.apply($, deferreds_catprofchange)
		.then(function() {
		    // console.log('appending profpane -> container', $profpane, $profpane_container);
		    $profpane_container
			.append($profpane);

		    $profpane.find(selectors.catui_device_container)
			.siblings(selectors.catui_device_loading_placeholder)
			.addClass('active')
			.siblings(':not(.active-exempt)')
			.removeClass('active');

		    var state = $.fn.HashHandle("hash"),
			cdev_search = function(cdevid) {
			    return $profpane
				.find(selectors.changes_cdev_has_cdev_id_ctx_devicelist_container)
				.filter(function() { return $(this).data('catdev') == cdevid; });
			}
		    if (('cdev' in state) && cdev_search(state.cdev).length == 1) {
			$profpane
			    .find(selectors.changes_cdev_with_cdev_id
				  .naive_format({cdev: state.cdev}))
			    .triggerHandler(events.change_cdev);
		    } else if (!!_catDev && cdev_search(_catDev.id).length == 1) {
			hashAct('cdev', _catDev.id, true);
		    } else if (cdev_search(catDeviceGuess).length == 1) {
			hashAct('cdev', catDeviceGuess, true);
		    } else {
			$profpane
			    .find(selectors.catui_device_no_match)
			    .addClass('active')
			    .siblings()
			    .removeClass('active');
		    }

		    $profpane
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

		}, function() { // on fail:
		    $profpane_error
	    		.addClass('active')
	    		.siblings().removeClass('active');
		});
    }

    $(selectors.changes_cdev_has_cdev_id_ctx_devicelist_container)
	.on('click', function (evt) {
	    evt.preventDefault();
	    var state = $.fn.HashHandle("hash"),
		key = 'cdev',
		val = $(this).attr('data-catdev');
	    if (!(key in state) || state[key] !== val) {
		hashAct(key, val);
	    }
	    return this;
	})
	.on(events.change_cdev, test_change_cdev);

    function test_change_cdev(evt) {
	    var button = this,
		device = $(button).data('_catdev');
	    catDev = (device instanceof CAT.Device().constructor) ?
		device : CAT.Device(catIdp.id,
				    $(button).data('catprof'),
	    			    $(button).data('catdev'));
	    var deferreds_catdevchange = [];
	    var $device_container = $(button)
		.parents(selectors.catui_profile_container)
		.find(selectors.catui_device_container);

	    $device_container
		.siblings(selectors.catui_device_loading_placeholder).addClass('active')
		.siblings(':not(.active-exempt)').removeClass('active');
	    // HACK!
	    $device_container.closest('.modal').scrollTop(0);

	    var cb_device = function(device_id,
				     device_display,
				     device_status,
				     device_eapcustomtext,
				     device_devicecustomtext,
				     device_message,
				     device_isredirect,
				     device_issigned,
				     device_redirect,
				     device_lang_display) {

		function setDeviceField(data_catui_val, text) {
		    var $el = $device_container
			.find('[data-catui="{0}"]'
			      .naive_format(data_catui_val));
		    if (!!text) {
			if (typeof text === 'string') {
			    // console.log('setting text', $el, text);
			    $el.removeClass('hidden').text(text);
			} else if (typeof text === 'function') {
			    // console.log('callback', $el, text);
			    $el.removeClass('hidden').each(text);
			}
		    } else {
			// console.log('hiding', $el);
			$el.addClass('hidden').empty();
		    }
		    return $el;
		}
		setDeviceField('device-display', device_display || device_id);
		setDeviceField('device-eapcustomtext', device_eapcustomtext);
		setDeviceField('device-devicecustomtext', device_devicecustomtext);
		setDeviceField('device-message',
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
							    CAT.API.localDownloadBase() +
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
		setDeviceField('device-redirectmessage',
			       device_isredirect ?
			       function() {
				   var device_redirect_url =
				       (device_redirect.search(/(https?:)?\/\//) == 0) ?
				       device_redirect : '//' + device_redirect;
				   $(this)
				       .find(
					   'a{0}'.naive_format(
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
					   'a{0}'.naive_format(
					       selectors.catui_device_redirecturl)
				       )
				       .removeAttr('href')
				       .text(null);
				   return this;
			       });
		setDeviceField('device-signed',
			       function() {
				   var act = !device_issigned ? 'addClass' : 'removeClass';
				   $(this)[act]('hidden');
				   return this;
			       });
		setDeviceField('device-language',
			       function() {
				   var act = !!!device_lang_display ? 'addClass' : 'removeClass';
				   $(this)
				       .text(device_lang_display || '')
				       .parent('span')[act]('hidden');
				   return this;
			       });
		if (!device_isredirect) {
		    setDeviceField('device-download',
				   function() {
				       $(this)
					   .removeClass('download-failed')
					   .find('button')
					   .removeClass('btn-danger')
					   .addClass('btn-success')
					   .data('_catdev', catDev)
					   .find(selectors.catui_dltxt_init)
					   .removeClass('hidden')
					   .siblings().addClass('hidden');
				   });
		}
		var deviceinfo_cb = function(device_deviceinfo) {
		    if (!!!device_deviceinfo) {
			setDeviceField('device-deviceinfo', function() {
			    $(this)
				.addClass('hidden')
				.find('.panel-body')
				.empty();
			});
			return null;
		    }
		    var sdf_deviceinfo = function() {
			var devinfo_id = 'deviceinfo_{0}_{1}'
			    .naive_format(
				$(this)
				    .closest(selectors.catui_profile_container)
				    .attr('id'),
				device_id);
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
		    }
		    setDeviceField('device-deviceinfo',
				   sdf_deviceinfo);
		}
		$.when(
		    catDev.getDeviceInfo()
		).then(deviceinfo_cb, deviceinfo_cb);
	    }
	    deferreds_catdevchange.push(
		$.when(
		    catDev.getDeviceID(),
		    catDev.getDisplay(),
		    catDev.getStatus(),
		    catDev.getEapCustomText(),
		    catDev.getDeviceCustomText(),
		    catDev.getMessage(),
		    catDev.isRedirect(),
		    catDev.isSigned(),
		    catDev.getRedirect(),
		    catDev.cat.getLanguageDisplay(catDev.lang)
		).then(cb_device, cb_device)
	    );

	    $.when.apply($, deferreds_catdevchange)
		.then(function() {
		    $device_container
			.addClass('active')
			.siblings(':not(.active-exempt)')
			.removeClass('active');
		}, function() {
		    // console.log('catdevchange master promise failed!', this, arguments);
		    $device_container
			.siblings(selectors.catui_device_load_error)
			.addClass('active')
			.siblings(':not(.active-exempt)')
			.removeClass('active');
		});

	    return this;
    }

    $('{0} button'.naive_format(selectors.catui_device_download))
	.on('click', function (evt) {
	    // evt.preventDefault();
	    var button = this,
		device = $(button).data('_catdev');
	    if (!(device instanceof CAT.Device().constructor)) {
		console.log('aborting! device is not a CAT.Device', device);
		return false;
	    }
	    $(button)
		.find(selectors.catui_dltxt_generate)
		.removeClass('hidden')
		.siblings().addClass('hidden');
	    var cb_dl = function(dlurl) {
		if (dlurl !== null) {
		    $(button)
			.find(selectors.catui_dltxt_download)
			.removeClass('hidden')
			.siblings().addClass('hidden');
		} else {
		    $(button)
			.removeClass('btn-success').addClass('btn-danger')
			.find(selectors.catui_dltxt_fail)
			  .removeClass('hidden')
			  .siblings().addClass('hidden')
			.end()
			.closest(selectors.catui_device_download)
			.addClass('download-failed');
		}
	    }
	    device.getDownload().then(cb_dl, cb_dl);
	    return this;
	});

    $('{0} button'.naive_format(selectors.catui_device_redirectmessage))
	.on('click', function (evt) {
	    // evt.preventDefault();
	    var button = this,
		$that = $(button)
		.closest(selectors.catui_device_redirectmessage)
		.find(selectors.catui_device_redirecturl),
		href = $that.attr('href'),
		target = $that.attr('target');
	    if ($that.length > 0 &&
		evt.target !== $that.get(0) &&
		href) {
		if (target == '_blank') {
		    window.open(href);
		} else {
		    window.location.href = href;
		}
	    }
	    return this;
	});

    $('{0} button'.naive_format(selectors.catui_device_message))
	.on('click', function (evt) {
	    $(this)
	    	.closest(selectors.catui_device_message)
		.addClass('catui-message-acknowledged');
	    return this;
	});

    var ap = appear({
	init: function() {
	    this.listProfilesQueue = [];
	    this.queueInterval = 100;
	    this.getQueueDelay = function(queueLength) {
		return (queueLength * this.queueInterval) - this.queueInterval;
	    }
	},
	elements: function() {
	    return $(selectors.toggles_modal_has_cidp_id)
		.get();
	},
	appear: function(el) {
    	    var $el = $(el),
    		catIdpID = parseInt($el.data('catidp'));
	    if (!!!catIdpID) {
		return undefined;
	    }
    	    var cb2 = function(ret) {
    	    	if (!(ret instanceof Array) ||
    	    	    ret.length == 0) {
    	    	    $el.triggerHandler(events.disable_noprofiles);
    	    	}
    	    }
	    var cb = function(ret) {
		if (!(ret instanceof Object) ||
		    !(catIdpID in ret)) {
		    $.when(
			CAT.API.listProfiles(catIdpID)
		    ).then(cb2, cb2);
		}
	    }
    	    this.listProfilesQueue.unshift(function() {
    		$.when(
    		    CAT.API.listAllIdentityProvidersByID()
    		).then(cb, cb);
	    });
	    var listProfilesQueue = this.listProfilesQueue,
		qcbDelay = this.getQueueDelay(listProfilesQueue.length);
	    setTimeout(function() {
		var qcb = listProfilesQueue.shift();
		if (typeof qcb === 'function') {
		    qcb();
		}
	    }, qcbDelay);
	    return this;
	}
    });

    CAT.API.touCallBack(function(tou) {
	var tou_url_start;
	if (!!tou && (tou_url_start = tou.search(/(https?:)?\/\//)) != -1) {
	    $(selectors.catui_cat_api_tou).attr('href', tou.substr(tou_url_start));
	}
    });

})(jQuery);
