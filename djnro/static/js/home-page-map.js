	var lat;
	var lng;
	var zoomLevel = 6;
	var latlng;
	var map;
	var bounds;
	var image;
	var imagePreProd;
	var infoWindow;
	var cityImg;
	var countryImg;
	var styles;
	var markersUrl;
	var pinImg;
	var pinImgPreProd;

	function initialize() {
		image = new google.maps.MarkerImage(pinImg,
			new google.maps.Size(50, 80),
			new google.maps.Point(0, 0),
			// The anchor for this image is the base of the flagpole at 18,42.
			new google.maps.Point(12, 40),
			new google.maps.Size(25, 40)
		);
		imagePreProd = new google.maps.MarkerImage(pinImgPreProd,
			new google.maps.Size(50, 80),
			new google.maps.Point(0, 0),
			new google.maps.Point(12, 40),
			new google.maps.Size(25, 40)
		);

		var styleArray = [ {
			featureType : "all",
			stylers : [ {
				saturation : -60
			}, {
				gamma : 1.00
			} ]
		}, {
			featureType : "poi.business",
			elementType : "labels",
			stylers : [ {
				visibility : "off"
			} ]
		}, {
			"featureType" : "transit.line",
			"elementType" : "geometry",
			"stylers" : [ {
				"visibility" : "off"
			} ]
		}, {
			"featureType" : "poi",
			"elementType" : "all",
			"stylers" : [ {
				"visibility" : "off"
			} ]
		}, {
			'featureType' : "administrative.country",
			'elementType' : "labels",
			'stylers' : [ {
				'visibility' : "off"
			} ]
		}

		];

		geocoder = new google.maps.Geocoder();
		// disable scrolling/draging in maps
		if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
			isDraggable = true;
			isScrollable = true;
		} else {
			isDraggable = true;
			isScrollable = true;
		}

		var mapOptions = {
			center : latlng,
			zoom : zoomLevel,
			mapTypeId : google.maps.MapTypeId.ROADMAP,
			styles : styleArray,
			mapTypeControlOptions : {
				style : google.maps.MapTypeControlStyle.DEFAULT
			},
			mapTypeControl : false,
			scrollwheel: isScrollable,
			draggable: isDraggable
		};
		map = new google.maps.Map(document.getElementById("map_canvas"),mapOptions);


		var homeControlDiv = document.createElement('div');
		homeControlDiv.className='roundButtonHolder';
		homeControlDiv.id="locationButton";
		var homeControl = new HomeControl(homeControlDiv, map);

		homeControlDiv.index = 1;
		map.controls[google.maps.ControlPosition.TOP_LEFT].push(homeControlDiv);

		bounds = new google.maps.LatLngBounds();
		infoWindow = new google.maps.InfoWindow();
		google.maps.event.addListener(map, 'idle', function() {
			center = map.getCenter();
			geocode(center);
			zoom = map.getZoom();
			if (zoom > 12){
				$("#showCityBtn").show();
				$("#showCountryBtn").hide();
			}
			else if ((zoom <= 12) && (zoom > 7)){
				$("#showCityBtn").hide();
				$("#showCountryBtn").show();
			}
			else {
				$("#showCityBtn").hide();
				$("#showCountryBtn").hide();
			}
		});

	}

	var markers = new Array();
	function placeMarkers() {
		$.get(markersUrl,
			function(data) {
				$.each(
					data,
					function(index, jsonMarker) {
						var marker = createMarker(jsonMarker);
						if (marker) {
							bounds.extend(marker.position);
								markers.push(marker);
								google.maps.event.addListener(
									marker,
									'click',
									function() {
										infoWindow.setContent ( "<div" + (jsonMarker.stage == 1 ? '' : ' class="preproduction"') + "><h4>"
												+ jsonMarker.inst
												+ "</h4>"
												+ "<div class='tabbable'>"
												+ "<ul class='nav nav-tabs'>"
												+ "<li class='active'><a href='#tab1' data-toggle='tab'>Info</a></li>"
												+ "<li><a href='#tab2' data-toggle='tab'>More...</a></li>"
												+ "</ul>"
												+ "<div class='tab-content'>"
												+ "<div class='tab-pane active' id='tab1'>"
												+ "<dl class='dl-horizontal'>"
												+ "<dt>Name</dt><dd>"
												+ jsonMarker.name
												+ "&nbsp;</dd>"
												+ "<dt>Address</dt><dd>"
												+ jsonMarker.address
												+ "&nbsp;</dd>"
												+ "<dt>Encryption</dt><dd>"
												+ jsonMarker.enc
												+ "&nbsp;</dd>"
												+ "<dt>SSID</dt><dd>"
												+ jsonMarker.SSID
												+ "&nbsp;</dd>"
												+ "<dt>Number of APs</dt><dd>"
												+ jsonMarker.AP_no
												+ "&nbsp;</dd>"
												+ (jsonMarker.stage == 1 ? '' : '<dt class="preproduction">Stage</dt><dd class="preproduction">Testing/Preproduction</dd>')
												+ "</dl>"
												+ "</div>"
												+ "<div class='tab-pane' id='tab2'>"
												+ "<dl class='dl-horizontal'>"
												+ "<dt>Port Restrict</dt><dd>"
												+ jsonMarker.port_restrict
												+ "&nbsp;</dd>"
												+ "<dt>transp_proxy</dt><dd>"
												+ jsonMarker.transp_proxy
												+ "&nbsp;</dd>"
												+ "<dt>IPv6</dt><dd>"
												+ jsonMarker.IPv6
												+ "&nbsp;</dd>"
												+ "<dt>NAT</dt><dd>"
												+ jsonMarker.NAT
												+ "&nbsp;</dd>"
												+ "<dt>Wired Number</dt><dd>"
												+ jsonMarker.wired_no
												+ "&nbsp;</dd></dl>"
												+ "</div>"
												+ "</div>"
												+ "</div>"
												+ "</div>");
										infoWindow.open(
											map,
											marker
										);
									});
								}
							});
							var mcOptions = {
								gridSize : 50,
								maxZoom : 15,
								styles : styles
							};
							var markerCluster = new MarkerClusterer(map,
									markers, mcOptions);
							map.fitBounds(bounds)
						});
	}

	function createMarker(markerObj) {
		var title = markerObj.name;
		var address = markerObj.address;
		var latLng = new google.maps.LatLng(markerObj.lat, markerObj.lng);
		var marker = new google.maps.Marker({
			'position' : latLng,
			'map' : map,
			'title' : title,
			'address' : address,
			'icon' : markerObj.stage == 1 ? image : imagePreProd,
		});
		return marker
	}

	function clusterMarkers(markers) {
		var markerCluster = new MarkerClusterer(map, markers);
	}

	function rad(x) {
		return x * Math.PI / 180;
	}

	function find_closest_marker(event) {
		var lat = event.latLng.lat();
		var lng = event.latLng.lng();
		var R = 6371; // radius of earth in km
		var distances = [];
		var closest = -1;
		for (i = 0; i < markers.length; i++) {
			var mlat = markers[i].position.lat();
			var mlng = markers[i].position.lng();
			var dLat = rad(mlat - lat);
			var dLong = rad(mlng - lng);
			var a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
					+ Math.cos(rad(lat)) * Math.cos(rad(lat))
					* Math.sin(dLong / 2) * Math.sin(dLong / 2);
			var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
			var d = R * c;
			distances[i] = d;
			if (closest == -1 || d < distances[closest]) {
				closest = i;
			}
		}

	}

	function geocode(position){
		addr = {};
		geocoder
		.geocode(
				{
					'latLng' : position
				},
				function(results, status) {
					if (status == google.maps.GeocoderStatus.OK) {
						if (results.length >= 1) {
							for ( var ii = 0; ii < results[0].address_components.length; ii++) {
								var street_number = route = street = city = state = zipcode = country = formatted_address = '';
								var types = results[0].address_components[ii].types
										.join(",");
								if (types == "sublocality,political"
										|| types == "locality,political"
										|| types == "neighborhood,political"
										|| types == "political") {
									addr.city = (city == '' || types == "locality,political") ? results[0].address_components[ii].long_name
											: city;
								}
								if (types == "country,political") {
									addr.country = results[0].address_components[ii].long_name;
								}
							}
						}
					}
				});
	}

	function codeAddress(address) {
	    geocoder.geocode( { 'address': address}, function(results, status) {
	      if (status == google.maps.GeocoderStatus.OK) {
	        map.setCenter(results[0].geometry.location);
	    	map.fitBounds(results[0].geometry.bounds)
	      } else {
	      }
	    });
	  }

	function HomeControl(controlDiv, map) {

		  // Set CSS styles for the DIV containing the control
		  // Setting padding to 5 px will offset the control
		  // from the edge of the map.
		  controlDiv.style.padding = '5px';

		  // Set CSS for the control border.
		  var controlUI = document.createElement('button');
		  controlUI.className='btn btn-warning roundButton';
		  controlUI.id = "showCityBtn";
		  extraCSS = 'background-image: url(' + cityImg + ');background-position: center center; background-repeat: no-repeat;';
		  controlUI.style.cssText='display:none; cursor:pointer; white-space:nowrap; position:absolute; '+extraCSS;
		  controlUI.title = "City View";

		  // Set CSS for the control border.
		  var controlUI2 = document.createElement('button');
		  controlUI2.className='btn btn-warning roundButton';
		  controlUI2.id = "showCountryBtn";
		  extraCSS2 = 'background-image: url(' + countryImg + ');background-position: center center; background-repeat: no-repeat;';
		  controlUI2.style.cssText='display:none; cursor:pointer; white-space:nowrap; position:absolute; '+extraCSS2;
		  controlUI2.title = "Country View";

		  controlDiv.appendChild(controlUI);
		  controlDiv.appendChild(controlUI2);

		  // Setup the click event listeners: simply set the map to Chicago.
		  google.maps.event.addDomListener(controlUI, 'click', function() {
		    codeAddress(addr.city+','+addr.country);
		  });
		  google.maps.event.addDomListener(controlUI2, 'click', function() {
			    codeAddress(addr.country);
			  });

		}

	function mapescape_callback(mapescape_active) {
	    var defControlOptions = {},
	    curControlOptions = {},
	    objCmp = function(a, b) {
		return JSON.stringify(a) == JSON.stringify(b);
	    }
	    for (var k in mapescapeControlOptions) {
		defControlOptions[k] = {};
		curControlOptions[k] = map[k];
	    }
	    if (mapescape_active &&
		!objCmp(curControlOptions, mapescapeControlOptions)) {
		map.setOptions(mapescapeControlOptions);
	    } else if (!mapescape_active &&
		       !objCmp(curControlOptions, defControlOptions)) {
		map.setOptions(defControlOptions);
	    }
	}

	$(document).ready(function() {
		mapDiv = $('#map_canvas')
		lat = mapDiv.data("map-center-lat");
		lat = parseFloat(lat.toString().replace(",","."));
		lng = mapDiv.data("map-center-lng");
		lng = parseFloat(lng.toString().replace(",","."));
		cityImg = mapDiv.data("city");
		countryImg = mapDiv.data("country");
		zoomLevel = 6;
		latlng = new google.maps.LatLng(lat,lng);
		map = '';
		bounds = '';
		image = '';
		infoWindow;
		pinImg = mapDiv.data("pin");
		pinImgPreProd = mapDiv.data("pin-preprod");
		pinGrpImg = mapDiv.data("group-pin");
		addr = {};
		styles = [{
			url : pinGrpImg,
			height : 54,
			width : 63,
			textColor : '#ffffff',
			textSize : 11
		}, {
			url : pinGrpImg,
			height : 54,
			width : 63,
			textColor : '#ffffff',
			textSize : 11
		}, {
			url : pinGrpImg,
			height : 54,
			width : 63,
			textColor : '#ffffff',
			textSize : 11
		}];
		mapescapeControlOptions = {
			zoomControlOptions: {
				position: google.maps.ControlPosition.LEFT_CENTER
			},
			streetViewControlOptions: {
				position: google.maps.ControlPosition.LEFT_CENTER
			}
		};

		markersUrl = mapDiv.data('markers');

		initialize();
		marks = placeMarkers();
		clusterMarkers(marks);
		$('#map_canvas').mapescape({
		    callback: mapescape_callback
		}).adapt_height(function($tgt, height) {
		    $tgt.css('max-height', height);
		});
	});

