	var lat;
	var lng;
	var zoomLevel;
	var latlng;
	var map;
	var bounds;
	var image;
	var marker;
	var eduMarker;
	var infoWindow;
	var getOnce;
	var geocoder;
	var infoWindow;
	var directionDisplay;
    var directionsService;
    var closestURL;

	var styles;
	var pinImg;

	function initialize() {
		image = new google.maps.MarkerImage(pinImg,
			new google.maps.Size(50, 80),
			new google.maps.Point(0, 0),
			// The anchor for this image is the base of the flagpole at 18,42.
			new google.maps.Point(12, 40),
			new google.maps.Size(25, 40)
		);
		var styleArray = [{
			featureType : "all",
			stylers : [{
				saturation : -60
			}, {
				gamma : 1.00
			}]
		}, {
			featureType : "poi.business",
			elementType : "labels",
			stylers : [{
				visibility : "off"
			}]
		}, {
			"featureType" : "transit.line",
			"elementType" : "geometry",
			"stylers" : [{
				"visibility" : "off"
			}]
		}, {
			"featureType" : "poi",
			"elementType" : "all",
			"stylers" : [{
				"visibility" : "off"
			}]
		}, {
			'featureType' : "administrative.country",
			'elementType' : "labels",
			'stylers' : [{
				'visibility' : "off"
			}]
		}];
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
		};
		map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);

		var input = document.getElementById('searchTextField');
	    var autocomplete = new google.maps.places.Autocomplete(input);

	    autocomplete.bindTo('bounds', map);

		infoWindow = new google.maps.InfoWindow();
		bounds = new google.maps.LatLngBounds();
		directionsDisplay = new google.maps.DirectionsRenderer();
		geocoder = new google.maps.Geocoder();
		directionsDisplay.setMap(map);

		if (getOnce == false) {
				marker = new google.maps.Marker({
					position : latlng,
					draggable : true,
					animation : google.maps.Animation.DROP,

				});
				marker.setMap(map);
			}
		google.maps.event.addListener(map, 'idle', function() {
			if(navigator.geolocation && getOnce == false) {
				navigator.geolocation.getCurrentPosition(getPosition);
			}

		});
		google.maps.event.addListener(map, 'click', function(event) {
			moveMarker(event.latLng);
		});
		google.maps.event.addListener(marker, 'dragend', function(event) {
			moveMarker(event.latLng);
		});

		google.maps.event.addListener(autocomplete, 'place_changed', function() {
			var place = autocomplete.getPlace();
			if (place.geometry.viewport) {
	            map.fitBounds(place.geometry.viewport);
	          } else {
	            map.setCenter(place.geometry.location);
	            map.setZoom(17);  // Why 17? Because it looks good.
	          }
			moveMarker(place.geometry.location);
		});
	}

	function calcRoute(start, end) {
		$("#distanceText").html();
        var request = {
            origin:start,
            destination:end,
            travelMode: google.maps.DirectionsTravelMode.WALKING
        };
        directionsService.route(request, function(response, status) {
          if (status == google.maps.DirectionsStatus.OK) {
            directionsDisplay.setDirections(response);
            var route = response.routes[0];
            var distText = route.legs[0].distance.text;
            $("#distanceText").html('Total distance: ' + distText);
          }
        });
      }

	function moveMarker(position) {
		marker.setPosition(position);
		getClosest(position);
	}

	function getPosition(position) {
		latlng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
		getOnce = true;
		map.setCenter(latlng);
		map.setZoom(12);
		marker.setPosition(latlng);
		getClosest(latlng);
	}

	function getClosest(coords){

		$.ajax({
			url: closestURL,
			data: {"lat": coords.lat(), "lng": coords.lng()},
			type: "GET",
			cache: false,
			success:function(data){
				bounds = new google.maps.LatLngBounds();
				if (eduMarker){
					eduMarker.setMap(null);
				}
				bounds.extend(coords);
				bounds.extend(new google.maps.LatLng(data.lat, data.lng));
				eduMarker = new google.maps.Marker({
					position : new google.maps.LatLng(data.lat, data.lng),
					draggable : true,
					'icon': image,
					animation : google.maps.Animation.DROP,

				});
				eduMarker.setMap(map);
				map.fitBounds(bounds);
				calcRoute(coords, new google.maps.LatLng(data.lat, data.lng));
				google.maps.event.addListener(
					eduMarker,
					'click',
					function() {
						infoWindow.setContent( "<div>"
							+ data.text
							+ "</div>"
						);
						infoWindow.open(
							map,
							eduMarker
						);
					});
				}
			});

	}

	function autocomplete() {
	    var input = $('#searchTextField');
	    var autocomplete = new google.maps.places.Autocomplete(input);
	    autocomplete.bindTo('bounds', map);
	    var marker = new google.maps.Marker({
	      map: map
	    });
	}

	function resizeMap()
	{

		if (map != undefined)
		{
			google.maps.event.trigger(map, 'resize');
		}

		return false;
	}

	$(document).ready(function() {
		var mapDiv = $('#map_canvas');
		lat = mapDiv.data('center-lat');
		lng = mapDiv.data('center-lng');
		lat = parseFloat(lat.toString().replace(",","."));
		lng = parseFloat(lng.toString().replace(",","."));
		var group = mapDiv.data('group');
		pinImg = mapDiv.data('pin');
		styles = [{
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
		}];
		closestURL = mapDiv.data('closest'),
		zoomLevel = 6;
		latlng = new google.maps.LatLng(lat, lng);
		map = '';
		bounds = '';
		image = '';
		marker = '';
		eduMarker = false;
		infoWindow;
		getOnce = false;
		geocoder = null;
		infoWindow;
		directionDisplay;
		directionsService = new google.maps.DirectionsService();
		initialize();
		resizeMap();
		$("#mylocm").click(function(){
			navigator.geolocation.getCurrentPosition(getPosition);
			return false;
		});

	});

	$(window).resize(function(){
		resizeMap();
	});
