	var lat = "";
	var lng = "";
	var zoomLevel = 6;
	var latlng;
	var map = '';
	var bounds = '';
	var image = '';
	var infoWindow;
	addr = {};
	var styles;
	var pinImg;
	var pinsUrl;
	var cityImg;
	var countryImg;

	function initialize() {
		image = new google.maps.MarkerImage(pinImg,
		// This marker is 29 pixels wide by 40 pixels tall.
		new google.maps.Size(29, 40),
		// The origin for this image is 0,0.
		new google.maps.Point(0, 0),
		// The anchor for this image is the base of the flagpole at 18,42.
		new google.maps.Point(14, 40));

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
			mapTypeId : google.maps.MapTypeId.ROADMAP,
			mapTypeControlOptions : {
				style : google.maps.MapTypeControlStyle.DEFAULT
			},
			navigationControl : true,
			mapTypeControl : false,
			scrollwheel: isScrollable,
			draggable: isDraggable
		};
		map = new google.maps.Map(document.getElementById("map_canvas"),
				mapOptions);


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
		$.get(
			pinsUrl,
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
									infoWindow.setContent(jsonMarker.text);
									infoWindow.open(
										map,
										marker
									);
								}
							);
						}
					}
				);
				var mcOptions = {
					gridSize : 60,
					maxZoom : null,
					styles : styles
				};

				var markerCluster = new MarkerClusterer(
					map,
					markers,
					mcOptions
				);
				map.fitBounds(bounds);
			}
		);
	}

	function createMarker(markerObj) {
		var latLng = new google.maps.LatLng(markerObj.lat, markerObj.lng);
		var marker = new google.maps.Marker({
			'position' : latLng,
			'map' : map,
			'icon' : image,
		});
		return marker
	}

	function clusterMarkers(markers) {
		var markerCluster = new MarkerClusterer(map, markers);
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
	        //alert("Geocode was not successful for the following reason: " + status);
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
		  extraCSS = 'background-image: url(' + cityImg +');background-position: center center; background-repeat: no-repeat;';
		  controlUI.style.cssText='display:none; cursor:pointer; white-space:nowrap; position:absolute; '+extraCSS;
		  controlUI.title = "City View";

		  // Set CSS for the control border.
		  var controlUI2 = document.createElement('button');
		  controlUI2.className='btn btn-warning roundButton';
		  controlUI2.id = "showCountryBtn";
		  extraCSS2 = 'background-image: url('+ countryImg + ');background-position: center center; background-repeat: no-repeat;';
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
		mapDiv = $('#map_canvas');
		lat = mapDiv.data('center-lat');
		lng = mapDiv.data('center-lng');
		lat = parseFloat(lat.toString().replace(",","."));
		lng = parseFloat(lng.toString().replace(",","."));
		latlng = new google.maps.LatLng(lat,lng);
		group = mapDiv.data('group');
		pinImg = mapDiv.data('pin');
		pinsUrl = mapDiv.data('url');
		cityImg = mapDiv.data('city');
		countryImg = mapDiv.data('country');
		styles = [ {
			url : group,
			height : 54,
			width : 63,
			textColor : '#ffffff',
			textSize : 11
		}, {
			url : group,
			height : 54,
			width : 63,
			textColor : '#ffffff',
			textSize : 11
		}, {
			url : group,
			height : 54,
			width : 63,
			textColor : '#ffffff',
			textSize : 11
		} ];
		mapescapeControlOptions = {
			zoomControlOptions: {
				position: google.maps.ControlPosition.LEFT_CENTER
			},
			streetViewControlOptions: {
				position: google.maps.ControlPosition.LEFT_CENTER
			}
		};
		initialize();
		marks = placeMarkers();
		clusterMarkers(marks);
		$('#map_canvas').mapescape({
		    callback: mapescape_callback
		}).adapt_height(function($tgt, height) {
		    $tgt.css('max-height', height);
		});
	});
