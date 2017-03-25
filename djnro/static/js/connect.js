;

function inst_search(evt) {
    if (evt.type == 'keyup') {
	switch (evt.keyCode) {
	case 27:
	    $(this).val('').trigger('input');
	    break;
	case 13:
	    if ($(this).val()) {
		var tofocus = $('ul.insts.match,ul.insts.filtered')
		    .find('li:not(:hidden):first > a');
		tofocus.focus();
		if (tofocus.closest('ul.insts.match').length == 1) {
		    // if single match does not have CAT data attribute
		    // trigger native click
		    if (tofocus.data('catidp')) {
			tofocus.trigger('click.cat_ui');
		    } else {
			tofocus.get(0).click();
		    }
		}
	    }
	    break;
	}
    }
    var needles = $('#inst-search-input')
	.val().trim().toLowerCase().split(/[\s,]+/);
    var shown = 0, hidden = 0;
    $('ul.insts li').each(function(index) {
	var elem = this,
	    $title_elem = $('.title', elem),
	    title = $title_elem.text().trim().toLowerCase(),
	    oper_name = ($title_elem.data('on') || '').trim()
	      .toLowerCase();
	if (needles.reduce(function(carry, item) {
	    var item_lc = item.toLowerCase();
	    return (carry &&
		    (item.length == 0 ||
		     title.indexOf(item_lc) > -1 ||
		     oper_name.indexOf(item_lc) > -1));
	}, true)) {
	    // $(this).show();
	    $(this).addClass('match');
	    shown += 1;
	} else {
	    // $(this).hide();
	    $(this).removeClass('match');
	    hidden += 1;
	}
    });
    if (shown == 1) {
	$('ul.insts').removeClass('filtered')
	    .addClass('match');
    } else if (hidden == 0) {
	$('ul.insts').removeClass('filtered')
	    .removeClass('match')
	    .children('li').removeClass('match');	
    } else {
	$('ul.insts').addClass('filtered')
	    .removeClass('match');
    }
}
$('#inst-search-input').on('keyup change', inst_search);

function insts_nav(evt) {
    var stop = true,
	evtype = {
	    keyup: 1,
	    keydown: 2
	};
    switch (evt.keyCode << evtype[evt.type]) {
    case 37 << evtype.keydown:
	// fall-through
    case 38 << evtype.keydown:
	$(this).parent().prevAll(':not(:hidden):first').children('a').focus();
	break;
    case 39 << evtype.keydown:
	// fall-through
    case 40 << evtype.keydown:
	$(this).parent().nextAll(':not(:hidden):first').children('a').focus();
	break;
    case 27 << evtype.keyup:
	$('#inst-search-input').focus();
	break;
    case 13 << evtype.keyup:
	// if click.cat_ui not bound, enter should trigger native this.click()
	$(this).trigger('click.cat_ui');
	break;
    default:
	stop = false;
    }
    if (stop) {
        evt.preventDefault();
    }
}
$('ul.insts li a').on('keyup keydown', insts_nav);

function geolocate() {
    var cb = function(pos) {
	var deferreds = [],
	    distance_max = 0,
	    distance_min = Infinity,
	    size_classes = ['btn-xs', 'btn-sm', '', 'btn-lg'];
	$('ul.insts li a').each(function() {
	    var that = this,
		cidp = $(this).data('_catidp'),
		d = new $.Deferred();
	    $(this).removeClass(size_classes.join(' '));
	    if (!!cidp &&
		('getDistanceFrom' in cidp) &&
		typeof cidp.getDistanceFrom === 'function') {
		var gdf_cb = function(ret) {
		    if (!(ret instanceof Array)) {
			d.reject(ret);
			return null;
		    }
		    var distance = Math.min.apply(null, ret);
		    if (isFinite(distance)) {
			distance_max = Math.max(distance_max, distance);
			distance_min = Math.min(distance_min, distance);
			$(that).data('_distance', distance);
			$('.distance', that)
			    .text(Math.round(distance).toString())
			    .parent()
			    .removeClass('hidden');
			d.resolve(ret);
		    } else {
			$(that).data('_distance', Infinity);
			$('.distance', that)
			    .parent()
			    .addClass('hidden');
			d.reject(ret);
		    }
		}
		$.when(
		    cidp.getDistanceFrom(pos.coords.latitude, pos.coords.longitude)
		).then(gdf_cb, gdf_cb);
	    } else {
		$(that).data('_distance', Infinity);
		$('.distance', that)
		    .parent()
		    .addClass('hidden');
		d.reject(null);
	    }
	    deferreds.push(d);
	});
	var sort_cb = function() {
	    var li_elements = $('ul.insts li');
	    li_elements.detach().each(function() {
		var $that = $(this).children('a');
		$that.removeClass(size_classes.join(' '));
		var distance = $that.data('_distance');
	    	var size_class;
	    	if (distance_max == distance_min) {
	    	    size_class = size_classes[3];
	    	} else if (!!distance &&
			   isFinite(distance)) {
	    	    size_class = Math.round(
			3-(3*
			   (distance - distance_min)/
			   (distance_max - distance_min))
		    );
	    	    size_class = size_classes[size_class];
	    	} else {
		    size_class = size_classes[0];
		}
	    	if (size_class) {
	    	    $that.addClass(size_class);
	    	}
	    }).sort(function(a, b) {
		a = $(a).children('a').data('_distance');
		b = $(b).children('a').data('_distance');
		return a - b;
	    });
	    $('ul.insts').append(li_elements);
	}
	$.when.apply($, deferreds)
	    .then(sort_cb, sort_cb);
	$('.trigger-geolocate').attr('disabled','disabled')
	    .children('a').attr('tabindex', -1);
    }
    navigator.geolocation.getCurrentPosition(cb);
}

$('.search-actions').on('click', '.trigger-geolocate[disabled] a', function(evt) {
    evt.preventDefault();
});

function populate_geo_cb() {
    var _this, _args, slocs_ret,
	geo = {};
    if (this instanceof Array) {
	_this = this[0];
	_args = arguments[0];
	slocs_ret = _args[0];
    } else {
	_this = this;
	_args = arguments;
	slocs_ret = _args[0];
    }
    
    if (!!_args[1] &&
	_args[1] == 'success' &&
	!!_this.dataType &&
	_this.dataType == 'json' &&
	slocs_ret instanceof Array) {

	slocs_ret.forEach(function(cur, idx) {
	    var inst_key = cur.inst_key;
	    var coords = {
		lat: parseFloat(cur.lat),
		lon: parseFloat(cur.lng)
	    }
	    if (!(inst_key in geo)) {
		geo[inst_key] = [coords];
	    } else if (geo[inst_key].find(function(cur) {
		return (JSON.stringify(cur) === JSON.stringify(coords));
	    }) === undefined) {
		geo[inst_key].push(coords);
	    }
	});
    }

    $('ul.insts > li > a').each(function() {
	var that = this,
	    iid = $(this).data('iid'),
	    _cidp = $(this).data('_catidp'),
	    _geo = {
		getDistanceFrom:
		!!CAT ?
		    CAT.IdentityProvider().constructor.prototype.getDistanceFrom :
		    getDistanceFrom,
		coord_sets: [],
		getGeo: function() {
		    var d = $.Deferred();
		    if (!!this.coord_sets.length > 0 &&
			(this.coord_sets[0] instanceof Array)) {
			return d.resolve(this.coord_sets[0]);
		    } else {
			return d.reject(null);
		    }
		}
	    }
	if (!!iid &&
	    (iid in geo)) {
	    _geo.coord_sets.push(geo[iid]);
	}
	if (_cidp instanceof CAT.IdentityProvider().constructor) {
	    var getgeo_cb = function(ret) {
		if (ret instanceof Array) {
		    _geo.coord_sets.unshift(ret);
		    return ret;
		}
	    }
	    $.when(
		_cidp.getGeo()
	    ).then(getgeo_cb, getgeo_cb);
	}
	$(this).data('_geo', _geo);
    });
}

function getDistanceFrom(lat, lon) {
    function deg2rad (deg) {
	return deg * ((1 / 180) * Math.PI);
    }
    var cb = function(ret) {
	if (ret instanceof Array) {
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
