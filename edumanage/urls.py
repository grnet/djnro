from django.conf.urls.defaults import *

urlpatterns = patterns('edumanage.views',
    url(r'^$', 'index', name="index"),
    url(r'^geolocate/?$', 'geolocate', name="geolocate"),
    url(r'^closest/?$', 'closest', name="closest"),
    url(r'^manage/?$', 'manage', name="manage"),

    url(r'^institutions/?$', 'institutions', name="institutions"),
    url(r'^institution/edit/(?P<institution_pk>\d+)?$', 'add_institution_details', name="edit-institution"),

    url(r'^services/(?P<service_pk>\d+)?$', 'services', name="services"),
    url(r'^services/del/?$', 'del_service', name="del-service"),
    url(r'^services/edit/(?P<service_pk>\d+)?$', 'add_services', name="edit-services"),
    url(r'^services/points/?$', 'get_service_points', name="get-service-points"),
    url(r'^services/allpoints/?$', 'get_all_services', name="get-all-services"),

    url(r'^servers/?$', 'servers', name="servers"),
    url(r'^servers/del/?$', 'del_server', name="del-server"),
    url(r'^servers/edit/(?P<server_pk>\d+)?$', 'add_server', name="edit-servers"),

    url(r'^realms/?$', 'realms', name="realms"),
    url(r'^realms/edit/(?P<realm_pk>\d+)?$', 'add_realm', name="edit-realms"),
    url(r'^realms/del/?$', 'del_realm', name="del-realm"),
    
    url(r'^contacts/?$', 'contacts', name="contacts"),
    url(r'^contacts/edit/(?P<contact_pk>\d+)?$', 'add_contact', name="edit-contacts"),
    url(r'^contacts/del/?$', 'del_contact', name="del-contact"),

    url(r'^adduser/?$', 'adduser', name="adduser"),
    
    url(r'^general/institution.xml', "instxml", name="instxml"),
    url(r'^general/realm.xml', "realmxml", name="realmxml"),
    

)

