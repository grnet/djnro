var lat;
var lng;
var zoomLevel = 8;
var latlng = new google.maps.LatLng(lat,lng);
var map = '';
var bounds = '';
var image = '';
var infoWindow;
var pinImg;
var styles;
var servicesUrl;
var servicesEditUrl;

function initialize() {
	image = new google.maps.MarkerImage(pinImg,
	// This marker is 29 pixels wide by 40 pixels tall.
	new google.maps.Size(29, 40),
	// The origin for this image is 0,0.
	new google.maps.Point(0,0),
	// The anchor for this image is the base of the flagpole at 18,42.
	new google.maps.Point(14, 40)
);
var styleArray = [
{
	featureType: "all",
	stylers: [
	{ saturation: -60 },
	{gamma: 1.00 }
	]
	},{
	featureType: "poi.business",
	elementType: "labels",
	stylers: [
	{ visibility: "off" }
	]
	},
	{ "featureType": "transit.line", "elementType": "geometry", "stylers": [ { "visibility": "off" } ] },
	{ "featureType": "poi", "elementType": "all", "stylers": [ { "visibility": "off" } ] },
	{'featureType': "administrative.country",
	'elementType': "labels",
	'stylers': [
	{ 'visibility': "off" }
	]}

];
var mapOptions = {
	center : latlng,
	zoom : zoomLevel,
	mapTypeId : google.maps.MapTypeId.ROADMAP,
	styles: styleArray,
	mapTypeId: google.maps.MapTypeId.ROADMAP,
	mapTypeControlOptions: {
	style: google.maps.MapTypeControlStyle.DEFAULT
	},
	navigationControl: true,
	mapTypeControl: false,
	};
	map = new google.maps.Map(document.getElementById("map_canvas"),
	mapOptions);

	bounds = new google.maps.LatLngBounds();
	infoWindow = new google.maps.InfoWindow();

}


function placeMarkers(){
var markers = new Array();
$.get(servicesUrl, function(data){
	$.each(data, function(index, jsonMarker) {
	var marker = createMarker(jsonMarker);
	if (marker){
	bounds.extend(marker.position);
	markers.push(marker);
	google.maps.event.addListener(marker, 'click', function() {
		infoWindow.setContent( "<div><h4>"+jsonMarker.name+"</h4>"+

	"<div class='tabbable'>"+
    "<ul class='nav nav-tabs'>"+
    "<li class='active'><a href='#tab1' data-toggle='tab'>Info</a></li>"+
    "<li><a href='#tab2' data-toggle='tab'>More...</a></li>"+
    "</ul>"+
    "<div class='tab-content'>"+
    "<div class='tab-pane active' id='tab1'>"+
    "<dl class='dl-horizontal'>"+
			"<dt>Name</dt><dd>"+jsonMarker.name+"&nbsp;</dd>"+
			"<dt>Address</dt><dd>"+jsonMarker.address+"&nbsp;</dd>"+
			"<dt>Encryption</dt><dd>"+jsonMarker.enc+"&nbsp;</dd>"+
			"<dt>SSID</dt><dd>"+jsonMarker.SSID+"&nbsp;</dd>"+
			"<dt>Number of APs</dt><dd>"+jsonMarker.AP_no+"&nbsp;</dd></dl>"+
    "</div>"+
    "<div class='tab-pane' id='tab2'>"+
    "<dl class='dl-horizontal'>"+
			"<dt>Port Restrict</dt><dd>"+jsonMarker.port_restrict+"&nbsp;</dd>"+
			"<dt>transp_proxy</dt><dd>"+jsonMarker.transp_proxy+"&nbsp;</dd>"+
			"<dt>IPv6</dt><dd>"+jsonMarker.IPv6+"&nbsp;</dd>"+
			"<dt>NAT</dt><dd>"+jsonMarker.NAT+"&nbsp;</dd>"+
			"<dt>Wired</dt><dd>"+jsonMarker.wired+"&nbsp;</dd></dl>"+
    "</div>"+
    "</div>"+
    "</div>"+
    "<div style='text-align:right;'><a href = '" + servicesEditUrl + jsonMarker.key + "' class='btn btn-primary'>Edit</a></div>"+
    "</div>");
		infoWindow.open(map,marker);
     });
	}
	});
	var mcOptions = {gridSize: 50, maxZoom: 15, styles: styles};



	var markerCluster = new MarkerClusterer(map, markers, mcOptions);
	map.fitBounds(bounds)
	});
	}

	function createMarker(markerObj){
	var title = markerObj.name;
	var latLng = new google.maps.LatLng(markerObj.lat, markerObj.lng);
	var marker = new google.maps.Marker({
	'position' : latLng,
	'map' : map,
	'title': title,
	'icon': image,
	});
	return marker;
	}

	function clusterMarkers(markers){
	var markerCluster = new MarkerClusterer(map, markers);
	}

	$(document).ready(function() {
		mapDiv = $('#map_canvas');
		lat = mapDiv.data('center-lat');
		lng = mapDiv.data('center-lng');
		lat = parseFloat(lat.toString().replace(",","."));
		lng = parseFloat(lng.toString().replace(",","."));
		pinImg = mapDiv.data('pin');
		groupImg = mapDiv.data('group');
		servicesUrl = mapDiv.data('service');
		servicesEditUrl = mapDiv.data('service-edit');
		console.log(servicesEditUrl);
		styles = [{
			url: groupImg,
			height: 54,
			width: 63,
			textColor: '#ffffff',
			textSize: 11
			},
			{
			url: groupImg,
			height: 54,
			width: 63,
			textColor: '#ffffff',
			textSize: 11
			},
			{
			url: groupImg,
			height: 54,
			width: 63,
			textColor: '#ffffff',
			textSize: 11
		}];
		initialize();
		marks = placeMarkers();
		clusterMarkers(marks);
	});
