;

/*
function BufferedQueue() {
  this.listeners = [];
  this.queue = [];
}

BufferedQueue.prototype = {
  getLast: function(cb) {
    this.queue.length > 0 ? cb(this.queue.shift()) : this.listeners.push(cb);
  },
  getFirst: function(cb) {
    this.queue.length > 0 ? cb(this.queue.shift()) : this.listeners.unshift(cb);
  },
  addLast: function(value) {
    if (this.listeners.length > 0) {
      this.listeners.shift()(value);
      return;
    }

    this.queue.push(value);
  },
  addFirst: function(value) {
    if (this.listeners.length > 0) {
      this.listeners.shift()(value);
      return;
    }

    this.queue.unshift(value);
  }
}
*/

$(document).ready(function() {

    /*
  $('#catModal').on('show.bs.modal', function(e) {
      var catIdp = new CatIdentityProvider(catApi,
                                           parseInt($(e.relatedTarget).data('catinstid')),
                                           catLang),
      modal = this;
      // e.preventDefault();
      console.log('catidp', catIdp);
      $.when(
          catIdp.getDisplay(),
          catIdp.getIcon(),
          catIdp.getProfiles()
      ).then(function(title, $icon, profiles) {
          console.log('show.bs.modal args', arguments);
          $(modal).find('[data-catui="institution"]').text(title);
          $(modal).find('[data-catui="container-logo"]').html($icon);
          // $(modal).modal('show');
      });
  });
    */

    var btoa = window.btoa || $.base64.btoa,
	atob = window.atob || $.base64.atob;
    function selector_encode(obj) {
	return btoa(JSON.stringify(obj)).replace(/=/g, '_');
    }
    function selector_decode(hash) {
	return JSON.parse(atob(hash.replace(/_/g, '=')));
    }

    var catIdp, catProf, _catProfO = {}, _catProf = [], catDev, _catDev;

    var ourevt = 'onpopstate' in window ? 'popstate' : 'hashchange';
    console.log('ourevt is '+ ourevt);
    if (ourevt == 'popstate') {
	console.log('pushState in history '+ ('pushState' in history) +' '+
		    'replaceState in history '+ ('replaceState' in history));
    }
    $(window).on(ourevt, function (evt) {
	// console.log('ourevt:', evt);
	// return true;
	var state = $.fn.HashHandle("hash"),
	    pairs = {
		cidp:  { evt: 'catIdpChange',  obj: catIdp  },
		cprof: { evt: 'catProfChange', obj: catProf },
		cdev:  { evt: 'catDevChange',  obj: catDev  }
	    }
	// console.log('ourevt objects:', catIdp, catProf, catDev,
	// 	    'state', state);
	console.log('ourevt objects: '+
		    typeof catIdp +' '+ (!!catIdp && catIdp.id)
		    +' '+
		    typeof catProf +' '+ (!!catProf && catProf.id)
		    +' '+
		    typeof catDev +' '+ (!!catDev && catDev.id)
		    +' '+
		    'state: '+
		    JSON.stringify(state));

	for (var key in pairs) {
	    var stateChange = 0;
	    if (!(key in state)) {
		if (typeof pairs[key].obj !== "undefined") {
		    stateChange = 2;
		}
	    }
	    else if (typeof pairs[key].obj === "undefined" ||
		     (state[key] != pairs[key].obj.id)) {
		// console.log('in '  + key + '=' +  state[key] + ', stateChange = 1, obj:',
		// 	    pairs[key].obj); 
		console.log('in '  + key + '=' +  state[key] + ', stateChange = 1, obj: '+
			    typeof pairs[key].obj +' '+ (!!pairs[key].obj && pairs[key].obj.id));
		stateChange = 1;
	    }
	    // console.log(key, 'stateChange:', stateChange);
	    console.log(key +' stateChange: '+ stateChange);
	    if (stateChange === 0) {
		continue;
	    }
	    switch (key) {
	    case 'cidp':
		if (stateChange === 2) {
		    catIdp = undefined;
		    $('.modal.in').modal('hide');
		} else {
		    return $('[data-toggle="modal"][data-catidp=' + state[key] + ']')
			.triggerHandler(pairs[key].evt);
		}
		// fallthrough if stateChange === 2
	    case 'cprof':
		if (stateChange === 2) {
		    if (key != 'cprof') {
			// _catProf = !!catProf && catProf || _catProf;
			if (!!catProf) {
			    var idx;
			    if ((idx = _catProf.indexOf(catProf.id)) != -1) {
				_catProf.splice(idx, 1);
			    } else {
				_catProfO[catProf.id] = catProf;
			    }
			    _catProf.unshift(catProf.id);
			}
			$.fn.HashHandle('removeHard', 'cprof');
		    }
		    catProf = undefined;
		} else {
		    return $('[data-toggle="tab"][data-catprof=' + state[key] + ']')
			.triggerHandler(pairs[key].evt);
		}
		// fallthrough if stateChange === 2
	    case 'cdev':
		if (stateChange === 2) {
		    if (key != 'cdev') {
			// console.log('_catDev = catDev', _catDev, catDev);
			_catDev = !!catDev && catDev || _catDev;
			$.fn.HashHandle('removeHard', 'cdev');
		    }
		    catDev = undefined;
		} else {
		    if (!('cprof' in state)) {
			console.log('have cdev but no cprof!!');
			break;
		    }
		    // console.log('triggering catDevChange');
		    var $catdev_trigger_el =
			$('[data-catprofpane="' +
			  state.cprof +
			  '"] [data-catdev="' +
			  state[key] + '"]');
		    if ($catdev_trigger_el.length == 1) {
		    	$catdev_trigger_el.triggerHandler(pairs[key].evt);
		    } else {
			$('[data-catprofpane="' +
			  state.cprof +
			  '"] [data-catui="device-no-match"]')
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
	$(window).trigger(ourevt);
    });

    function hashAct(key, val, hard) {
	var state = $.fn.HashHandle('hash'),
	    hard = !!hard && 'Hard' || '';
	if (key in state) {
	    if (state[key] == val || typeof val === 'undefined') {
		console.log('hashAct', 'remove' + hard, key);
		$.fn.HashHandle('remove' + hard, key);
	    } else {
		console.log('hashAct', 'add' + hard, key, val);
		$.fn.HashHandle('add' + hard, key, val);
	    }
	} else {
	    console.log('hashAct', 'add' + hard, key, val);
	    $.fn.HashHandle('add' + hard, key, val);
	}
    }

    $('[data-catui="container-logo"],[data-catui="container-support"]')
	.on('hide.logosup.cat', function (evt) {
	    $(this).addClass('hidden');
	    return this;
	})
	.on('show.logosup.cat', function (evt) {
	    $(this).removeClass('hidden');
	    return this;
	});
    $('[data-toggle="modal"][data-catidp]')
	.on('click', function (evt) {
	    evt.preventDefault();
	    var key = 'cidp',
		val = $(this).attr('data-catidp');
	    // console.log($(this), key, val);
	    hashAct(key, val);
	    return this;
	})
	.on('disableNoProfiles', function (evt) {
	    evt.preventDefault();
	    $(this)
		.attr('disabled', 'disabled')
		.children('.badge').removeClass('hidden');
	    return this;
	})
	.on('catIdpChange', function (evt) {
	    // console.log('catIdpChange:', this, arguments);
	    var button = this,
		$modal = $('.modal#' + $(button).data('target'));
	    $modal.on('hidden.bs.modal', function(evt) {
		var state = $.fn.HashHandle('hash');
		if ('cidp' in state) {
		    // hashHandle remove cidp
		    hashAct('cidp');
		}
		return this;
	    });
	    $('[data-catui="container-logo"],[data-catui="container-support"]')
		.triggerHandler('hide.logosup.cat');
	    catIdp = $(button).data('_catidp');
	    if (!(catIdp instanceof CatIdentityProvider)) {
		catIdp = new CatIdentityProvider(catApi,
						 parseInt($(button).data('catidp')),
						 catLang);
		$(button).data('_catidp', catIdp);
	    }
	    // var cb_profiles = function(profiles)
	    var cb = function(title, $icon, profiles) {
		console.log('catIdpChange cb:', arguments);
		var args = Array.prototype.slice.call(arguments);
		if (profiles === null ||
		    !(profiles instanceof Array) ||
		    profiles.length == 0) {
		    $(button).triggerHandler('disableNoProfiles');
		    // avoid async catIdp.getEntityID() for now
		    // hashhandle removeHard cidp
		    hashAct('cidp', catIdp.id, true);
		    // hashAct('cidp', undefined, true);
		    return this;
		}
		var $profsel_container = $modal
		    .find('[data-catui="profile-select-container"]'),
		    $profsel_template = $profsel_container.find('> :first-child');
		var $profsels = [];
		var profiles_byid = {};
		for (var idx=0; idx < profiles.length; idx++) {
		    profiles_byid[profiles[idx].getProfileID()] = profiles[idx];
		    // console.log("profile:", idx, profiles[idx]);
		    // also clone bound events!!!!
		    var $profsel_el = $profsel_template.clone(true),
			$profsel_a = $profsel_el.find('> [data-catprof]');
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
			      '[data-catprofpane="' +
			      profiles[idx].getProfileID() +
			      '"]')
			.attr('href',
			      '#cat-' + selector_encode({cidp: profiles[idx].getIdpID(),
							 cprof: profiles[idx].getProfileID()}));
		    // '#cidp-' + profiles[idx].getIdpID() +
		    // ',cprof-' + profiles[idx].getProfileID()); // jQuery limitation
		    $profsels.push($profsel_el);
		}
		$profsel_container
		    .html($profsels)
		    .addClass('hidden');
		//[($profsels.length == 1) ? 'addClass' : 'removeClass']('hidden');

		var state = $.fn.HashHandle("hash");
		if (('cprof' in state) && (state.cprof in profiles_byid)) {
		    $profsel_container
			.find('[data-catprof="' + state.cprof + '"]')
			.triggerHandler('catProfChange');
		// } else if (!!_catProf && (_catProf.id in profiles_byid)) {
		} else {
		    for (var _idx = 0;
			 _idx < _catProf.length && !(_catProf[_idx] in profiles_byid);
			 _idx++); // empty statement
		    if (_idx < _catProf.length) {
			$profsel_container
		    	    .find('[data-catprof="' + _catProf[_idx] + '"]')
		    	    .data('_catprof', _catProfO[_catProf[_idx]]);
			    // .triggerHandler('catProfChange');
			hashAct('cprof', _catProf[_idx], true);
		    } else {
			hashAct('cprof', profiles[0].getProfileID(), true);
		    }
		}
		if (!!title) {
		    $modal.find('[data-catui="institution"]').text(title);
		    if ($icon instanceof $) {
			$icon.attr({title: title, alt: title});
		    }
		} else {
		    $modal.find('[data-catui="institution"]').html('&nbsp;');
		}
		$modal.find('[data-catui="container-logo"]')
		    .html($icon)
		    .triggerHandler(
			$icon !== null ? 'show.logosup.cat' : 'hide.logosup.cat'
		    );

		$modal.modal('show');
		return this;
	    }
	    return $.when(
		catIdp.getDisplay(),
		catIdp.getIcon(),
		catIdp.getProfiles(true)
	    ).then(cb, cb);	    
	});
    $('[data-toggle="tab"][data-catprof]')
	.on('click', function (evt) {
	    evt.preventDefault();
	    if ($(this).parent().hasClass('active')) {
		return this;
	    }
	    // console.log('data-toggle=tab click fired');
	    var key = 'cprof',
		val = $(this).attr('data-catprof');
	    // console.log($(this), key, val);
	    hashAct(key, val);
	    return this;
	})
	.on('catProfChange', function (evt) {
	    console.log('catProfChange fired', this, arguments);
 	    var button = this,
		profile = $(button).data('_catprof');
	    catProf = (profile instanceof CatProfile) ?
		profile : new CatProfile(catApi,
	    				 catIdp.id,
	    				 parseInt($(button).data('catprof')),
	    				 catLang);
	    var deferreds_catprofchange = [];

	    $(button).parent('li')
	    	.addClass('active')
	    	.siblings().removeClass('active');

	    $('[data-catui="container-support"]')
		.triggerHandler('hide.logosup.cat');
	    var $support_container = $('[data-catui="support-contact-container"]'),
		$supportel_template = $support_container.find('> span:first-child');
	    var cb_support = function(local_url, local_email, local_phone) {
		function toggleSupportElements($supcon, hasSupport) {
		    var answer =     !!hasSupport ? 'yes' : 'no',
			answer_inv = !!hasSupport ? 'no' : 'yes',
			toggle =     { yes: 'addClass', no: 'removeClass' };
		    // console.log('toggleSupportElements',
		    // 		'answer', answer,
		    // 		'answer_inv', answer_inv);
		    // console.log($supcon.get(), toggle[answer_inv], 'hidden');
		    $supcon[toggle[answer_inv]]('hidden')
			.siblings().each(function() {
			    if ($(this).data('catui-support') === answer) {
				// console.log('1:', this,
				// 	    toggle[!!hasSupport ? answer_inv : answer], 'hidden');
				$(this)[toggle[!!hasSupport ? answer_inv : answer]]('hidden');
			    }
			    if ($(this).data('catui-support') === answer_inv) {
				// console.log('2:', this,
				// 	    toggle[!!hasSupport ? answer : answer_inv], 'hidden');
				$(this)[toggle[!!hasSupport ? answer : answer_inv]]('hidden');
			    }
			});
		    // return this;
		}
		if (!!!local_url &&
		    !!!local_email &&
		    !!!local_phone) {
		    toggleSupportElements($support_container, false);
		    $('[data-catui="container-support"]')
			.triggerHandler('show.logosup.cat');
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
		    $('[data-catui="container-support"]')
			.triggerHandler('show.logosup.cat');
		    return this;
		}
	    }
	    // deferreds_catprofchange.push(
		$.when(
		    catProf.getLocalUrl(),
		    catProf.getLocalEmail(),
		    catProf.getLocalPhone()
		).then(cb_support, cb_support);
	    // );

	    var $profpane_container = $(button).parents('.modal')
		.find('[data-catui="profiles-container"]'),
		$profpane_template = $profpane_container.find('[data-catui="profile-container-template"]'),
		$profpane_loading = $profpane_container.find('[data-catui="profile-loading-placeholder"]'),
		$profpane_error = $profpane_container.find('[data-catui="profile-load-error"]');

	    $profpane_loading
	    	.addClass('active')
	    	.siblings().removeClass('active');

	    var $profpane = $profpane_container
		.find('[data-catui="profile-container"][data-catprofpane="' +
		      catProf.getProfileID() +
		     '"]');
	    if ($profpane.length == 1) {
		console.log('found profpane!');
		// $(button).tab('show');
		$profpane
	    	    .addClass('active')
	    	    .siblings().removeClass('active');
		$('[data-catui="profile-select-container"]')
		    .children()
		    .each(function(idx, el) {
			// console.log('each', idx, el);
		    	$(this).parent().addClass('hidden');
		    	if (idx > 0) {
		    	    $(this).parent().removeClass('hidden');
		    	    return false;
		    	}
			return this;
		    });

		$profpane.find('[data-catui="device-container"]')
		    .siblings('[data-catui="device-loading-placeholder"]').addClass('active')
		    .siblings(':not(.active-exempt)').removeClass('active');

		var state = $.fn.HashHandle("hash"),
		    cdev_search = function(cdevid) {
			return $profpane
			    .find('[data-catui="devicelist-container"] [data-catdev]')
			    .filter(function() { return $(this).data('catdev') == cdevid; });
		    }
		if (('cdev' in state) && cdev_search(state.cdev).length == 1) {
		    console.log('found profpane, cdev in state');
		    $profpane
			.find('[data-catdev="' + state.cdev + '"]')
			.triggerHandler('catDevChange');
		} else if (!!_catDev && cdev_search(_catDev.id).length == 1) {
		    console.log('found profpane, _catDev:', _catDev);
		    // $profpane
		    // 	.find('[data-catdev="' + _catDev.id + '"]')
		    // 	.data('_catdev', _catDev);
			// .triggerHandler('catDevChange');
		    hashAct('cdev', _catDev.id, true);
		} else if (cdev_search(catDeviceGuess).length == 1) {
		    console.log('found profpane, cdev = catDeviceGuess');
		    hashAct('cdev', catDeviceGuess, true);
		} else {
		    $profpane
			.find('[data-catui="device-no-match"]')
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
		var $description_element = $profpane.find('[data-catui="profile-description"]');
		if (!!description) {
		    $description_element.text(description);
		} else {
		    $description_element.html('&nbsp;');
		}
		// if profiles <= 1 or profile title == description, hide description
		if ($('[data-catui="profile-select-container"]').children().length <= 1 ||
		    $(button).text() == description) {
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
		    return CatDevice.groupDevices(devices);
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
		var $devicelist_container = $profpane.find('[data-catui="devicelist-container"]'),
		    $devicegroup_heading_template = $devicelist_container.find('.panel-heading'),
		    $devicegroup_template = $devicegroup_heading_template.next(),
		    $device_template = $devicegroup_template.find('.list-group-item').first();
		// console.log('cb2 devicelist:', $devicelist_container, $devicegroup_heading_template, $devicegroup_template);
		// $devicelist_container
		//     .find('.panel-group')
		//     .attr('id', $profpane.attr('id'));
		var devgroups = [],
		    devgroup_id_from = $devicegroup_template.attr('id'),
		    ungrouped_devices = {};
		for (var devgroup in grouped_devices) {
		    var $devgroup_heading = $devicegroup_heading_template.clone(true);
		    var devgroup_id_to = devgroup_id_from.replace('_Dummy', '_' + devgroup);
		    $devgroup_heading
			.attr('id', function(idx, cur) {
			    return cur.replace(devgroup_id_from, devgroup_id_to);
			})
			.find('a')
			.attr({ 'data-target': '#' + devgroup_id_to + '_' + $profpane.attr('id'),
				'data-toggle': 'collapse-noanimation',
				'aria-controls': devgroup_id_to + '_' + $profpane.attr('id') })
			.text(devgroup);
		    $devgroup = $devicegroup_template.clone(true);
		    $devgroup
			.attr('id', devgroup_id_to + '_' + $profpane.attr('id'))
			.attr('aria-labelledby', function(idx, cur) {
			    return cur.replace(devgroup_id_from, devgroup_id_to + '_' + $profpane.attr('id'));
			});
		    var devs = [];
		    for (var devidx = 0; devidx < grouped_devices[devgroup].length; devidx++) {
			var $device = $device_template.clone(true),
			    device_id = grouped_devices[devgroup][devidx].getDeviceID();
			ungrouped_devices[device_id] = grouped_devices[devgroup][devidx];
			$device.children('a')
			    .data('_catdev', grouped_devices[devgroup][devidx])
			    .attr('href',
				  '#cat-' + selector_encode({cidp: catProf.getIdpID(),
							     cprof: catProf.getProfileID(),
							     cdev: device_id}))
			    .attr('data-catdev', device_id);
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
		    // console.log(devgroup + ': ', $devgroup);
		    devgroups.push($devgroup_heading, $devgroup);
		}
		$devicelist_container
		    .find('.panel')
		    .html(devgroups);
		// $devicelist_container
		//     .find('.collapse').collapse({toggle: false});
	    }
	    deferreds_catprofchange.push(
		$.when(
		    catProf.getDevices()
		).then(cb_devicelist, cb_devicelist)
		    .then(cb_devicelist_final, cb_devicelist_final)
	    );

	    $.when.apply($, deferreds_catprofchange)
		.then(function() {
		    console.log('appending profpane -> container', $profpane, $profpane_container);
		    $profpane_container
			// .find('[data-catui="profile-container"]')
			//   .remove()
			// .end()
			.append($profpane);
		    // $(button).tab('show');

		    $profpane.find('[data-catui="device-container"]')
			.siblings('[data-catui="device-loading-placeholder"]')
			.addClass('active')
			.siblings(':not(.active-exempt)')
			.removeClass('active');

		    var state = $.fn.HashHandle("hash"),
			cdev_search = function(cdevid) {
			    return $profpane
				.find('[data-catui="devicelist-container"] [data-catdev]')
				.filter(function() { return $(this).data('catdev') == cdevid; });
			}
		    if (('cdev' in state) && cdev_search(state.cdev).length == 1) {
			console.log('kokolala1');
			$profpane
			    .find('[data-catdev="' + state.cdev + '"]')
			    .triggerHandler('catDevChange');
		    } else if (!!_catDev && cdev_search(_catDev.id).length == 1) {
			console.log('kokolala2');
			// $profpane
			//     .find('[data-catdev="' + _catDev.id + '"]')
			//     .data('_catdev', _catDev);
			// .triggerHandler('catDevChange');
			hashAct('cdev', _catDev.id, true);
		    } else if (cdev_search(catDeviceGuess).length == 1) {
			console.log('kokolala3');
			hashAct('cdev', catDeviceGuess, true);
		    } else {
			$profpane
			    .find('[data-catui="device-no-match"]')
			    .addClass('active')
			    .siblings()
			    .removeClass('active');
		    }

		    $profpane
	    		.addClass('active')
	    		.siblings().removeClass('active');

		    $('[data-catui="profile-select-container"]')
		    	.children()
		    	.each(function(idx, el) {
			    // console.log('each', idx, el);
		    	    $(this).parent().addClass('hidden');
		    	    if (idx > 0) {
		    		$(this).parent().removeClass('hidden');
		    		return false;
		    	    }
			    return this;
		    	});
		    // return this;
		}, function() { // on fail:
		    $profpane_error
	    		.addClass('active')
	    		.siblings().removeClass('active');
		});
	});
    $(document)
	.on('click',
	    '[data-toggle="collapse-noanimation"]',
	    function(evt) {
		// console.log('evt: ', evt);
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
    // propagate clicks to the device group/device info headings, device selectors from their container elements
    $(document)
	.on('click',
	    '[data-catui="devicelist-container"] .panel-heading, [data-catui="device-deviceinfo"] .panel-heading, [data-catui="devicelist-container"] .list-group-item',
	    function (evt) {
		var $that = $(this).find('[data-toggle="collapse-noanimation"],[data-catdev]');
		if ($that.length > 0 &&
		    evt.target !== $that.get(0) &&
		    $that.find(evt.target).length == 0) {
		    // console.log('clicking!', this, $that.get(0));
		    return $that.trigger('click');
		}
		return this;
	    });
    // hiding other device groups upon device group selection
    // workaround for collapse data-parent not working
    $(document)
	.on('click', '[data-catui="devicelist-container"] [data-toggle="collapse-noanimation"]', function (evt) {
	    // console.log('devgroup click:', this, evt);
	    $(this)
		.parent('.panel-heading')
		.siblings($(this).data('target'))
		.siblings('.panel-collapse.in')
		.removeClass('in');
		// .each(function() {
		//     $(this).collapse('toggle');
		// });
	    return this;
	});
    $('[data-catui="devicelist-container"] [data-catdev]')
	.on('click', function (evt) {
	    evt.preventDefault();
	    // console.log('[data-catdev] click:', $(this));
	    var state = $.fn.HashHandle("hash"),
		key = 'cdev',
		val = $(this).attr('data-catdev');
	    if (!(key in state) || state[key] !== val) {
		hashAct(key, val);
	    }
	    return this;
	})
	.on('catDevChange', function (evt) {
	    console.log('catDevChange fired', this, arguments);
	    var button = this,
		device = $(button).data('_catdev');
	    catDev = (device instanceof CatDevice) ?
		device : new CatDevice(catApi,
	    			       catIdp.id,
	    			       $(button).data('catdev'),
	    			       catLang);
	    // console.log('catDev is now', catDev);
	    var deferreds_catdevchange = [];
	    var $device_container = $(button)
		.parents('[data-catui="profile-container"]')
		.find('[data-catui="device-container"]');
	    // console.log('device container', $device_container);

	    $device_container
		.siblings('[data-catui="device-loading-placeholder"]').addClass('active')
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

		// return $.Deferred().reject('kokolala').promise();

		function setDeviceField(data_catui_val, text) {
		    var $el = $device_container
			.find('[data-catui="' + data_catui_val + '"]');
		    if (!!text) {
			if (typeof text === 'string') {
			    console.log('setting text', $el, text);
			    $el.removeClass('hidden').text(text);
			} else if (typeof text === 'function') {
			    console.log('callback', $el, text);
			    $el.removeClass('hidden').each(text);
			}
		    } else {
			console.log('hiding', $el);
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
							    catApi.localDownloadBase() +
							    href.substr(href_slash_idx + 1));
					   }
					   return this;
				       });
				   $(this)
				       // .find('button[disabled]')
				       //   .removeAttr('disabled')
				       //   .end()
				       // .siblings('[data-catui="device-download"]')
				       // .find('button')
				       // .attr('disabled', 'disabled');
				       .removeClass('catui-message-acknowledged');
			       } :
			       function() {
				   $(this).addClass('hidden');
				   $(this)
				   //     .siblings('[data-catui="device-download"]')
				   //     .find('button')
				   //     .removeAttr('disabled');
				       .removeClass('catui-message-acknowledged');
				   return this;
			       });
		setDeviceField('device-redirectmessage',
			       device_isredirect ?
			       function() {
				   var device_redirect_url =
				       (device_redirect.search(/(https?:)?\/\//) == 0) ?
				       device_redirect : '//' + device_redirect;
				   $(this).find('a[data-catui="device-redirecturl"]')
				       .attr('href', device_redirect_url)
				       .text(device_redirect);
				   return this;
			       } :
			       function() {
				   $(this).
				       addClass('hidden')
				       .find('a[data-catui="device-redirecturl"]')
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
					   .find('[data-catui-dltxt="init"]')
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
			var devinfo_id = 'deviceinfo_' +
			    $(this)
			    .closest('[data-catui="profile-container"]')
			    .attr('id') +
			    '_' + device_id;
			$(this)
			    .removeClass('hidden')
			    .find('.panel-heading')
			      .attr('id', 'heading_' + devinfo_id)
			      .find('a')
			        .attr({ 'data-target': '#' + devinfo_id,
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
		    console.log('catdevchange master promise failed!', this, arguments);
		    $device_container
			.siblings('[data-catui="device-load-error"]')
			.addClass('active')
			.siblings(':not(.active-exempt)')
			.removeClass('active');
		});

	    return this;
	});
    $('[data-catui="device-download"] button')
	.on('click', function (evt) {
	    console.log('click.catDownload fired', this, arguments);
	    // evt.preventDefault();
	    var button = this,
		device = $(button).data('_catdev');
	    if (!(device instanceof CatDevice)) {
		console.log('aborting! device is not a CatDevice', device);
		return false;
	    }
	    $(button)
		.find('[data-catui-dltxt="generate"]')
		.removeClass('hidden')
		.siblings().addClass('hidden');
	    var cb_dl = function(dlurl) {
		if (dlurl !== null) {
		    $(button)
			.find('[data-catui-dltxt="download"]')
			.removeClass('hidden')
			.siblings().addClass('hidden');
		    // console.log('downloading has begun:', dlurl);
		} else {
		    $(button)
			.removeClass('btn-success').addClass('btn-danger')
			.find('[data-catui-dltxt="fail"]')
			  .removeClass('hidden')
			  .siblings().addClass('hidden')
			.end()
			.closest('[data-catui="device-download"]')
			.addClass('download-failed');
		    // console.log('downloading has failed!', dlurl);
		}
	    }
	    device.getDownload().then(cb_dl, cb_dl);
	    return this;
	});
    $('[data-catui="device-redirectmessage"] button')
	.on('click', function (evt) {
	    // evt.preventDefault();
	    var button = this,
		$that = $(button)
		.closest('[data-catui="device-redirectmessage"]')
		.find('[data-catui="device-redirecturl"]'),
		href = $that.attr('href'),
		target = $that.attr('target');
	    if ($that.length > 0 &&
		evt.target !== $that.get(0) &&
		href) {
		console.log('simulating clicking!', $that);
		if (target == '_blank') {
		    window.open(href);
		} else {
		    window.location.href = href;
		}
	    }
	    return this;
	});
    $('[data-catui="device-message"] button')
	.on('click', function (evt) {
	    // evt.preventDefault();
	    // var button = this;
	    // 	$that = $(button)
	    // 	.closest('[data-catui="device-message"]')
	    // 	.siblings('[data-catui="device-download"]')
	    // 	.find('button[disabled]');
	    // if ($that.length > 0 &&
	    // 	evt.target !== $that.get(0)) {
	    // 	console.log('enabling download!', $that);
	    // 	$(button).attr('disabled', 'disabled');
	    // 	$that.removeAttr('disabled');
	    // }
	    $(this)
	    	.closest('[data-catui="device-message"]')
		.addClass('catui-message-acknowledged');
	    return this;
	});

    var ap = appear({
	init: function() {
	    // this.listProfilesQueue = new BufferedQueue();
	    this.listProfilesQueue = [];
	    this.queueInterval = 200;
	    this.getQueueDelay = function(queueLength) {
		return (queueLength * this.queueInterval) - this.queueInterval;
		// if (!!!this.queueDelay) {
		//     this.queueDelay = this.queueInterval;
		// }
		// this.queueDelay =
		//     Math.min(12000,
		// 	     Math.max(300,
		// 		      this.queueDelay +
		// 		      ((Math.pow(2, queueLength) - 2) * -300)
		// 		     )
		// 	    );
		// return this.queueDelay;
	    }
	},
	elements: function() {
	    return $('[data-toggle="modal"][data-catidp]:not([disabled])')
		.get();
	},
	appear: function(el) {
    	    var $el = $(el),
    		catIdpID = parseInt($el.data('catidp'));
	    if (!!!catIdpID) {
		return undefined;
	    }
	    if (!($el.data('_catidp') instanceof CatIdentityProvider)) {
		$el.data('_catidp', new CatIdentityProvider(catApi,
							    catIdpID,
							    catLang)
			);
	    }
	    // checking = $el.parents('address').children('strong').text();
    	    var cb = function(ret) {
    	    	if (!(ret instanceof Array) ||
    	    	    ret.length == 0) {
    	    	    // console.log('disabling button for:',
    	    	    // 		catIdpID,
    	    	    // 		$el.parents('address').children('strong').text());
    	    	    $el.triggerHandler('disableNoProfiles');
    	    	}
    	    }
    	    // this.listProfilesQueue.addFirst(function() {
    	    this.listProfilesQueue.unshift(function() {
    		$.when(
    		    catApi.listProfiles(catIdpID, catLang)
    		).then(cb, cb);
	    });
	    var listProfilesQueue = this.listProfilesQueue,
		// qcbDelay = this.getQueueDelay(listProfilesQueue.queue.length);
		qcbDelay = this.getQueueDelay(listProfilesQueue.length);
	    console.log('qcbDelay', qcbDelay);
	    setTimeout(function() {
		// listProfilesQueue.getFirst(function(qcb) {
		//     qcb();
		// });
		var qcb = listProfilesQueue.shift();
		if (typeof qcb === 'function') {
		    qcb();
		}
	    }, qcbDelay);
	    return this;
	}
    });

    catApi.touCallBack(function(tou) {
	var tou_url_start;
	if (!!tou && (tou_url_start = tou.search(/(https?:)?\/\//)) != -1) {
	    $('[data-catui="cat-api-tou"]').attr('href', tou.substr(tou_url_start));
	}
    });
});
