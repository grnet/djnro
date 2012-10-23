from django.conf.urls.defaults import *

urlpatterns = patterns('edumanage.views',
    url(r'^$', 'index', name="index"),
    url(r'^geolocate/?$', 'geolocate', name="geolocate"),
    url(r'^closest/?$', 'closest', name="closest"),
    
    url(r'^general/institution.xml', "instxml", name="instxml"),
    url(r'^general/realm.xml', "realmxml", name="realmxml"),
    url(r'^general/realm_data.xml', "realmdataxml", name="realmdataxml"),
    
    url(r'^manage/?$', 'manage', name="manage"),
    
    
    url(r'^manage/institutions/?$', 'institutions', name="institutions"),
    url(r'^manage/institution/edit/(?P<institution_pk>\d+)?$', 'add_institution_details', name="edit-institution"),

    url(r'^manage/services/(?P<service_pk>\d+)?$', 'services', name="services"),
    url(r'^manage/services/del/?$', 'del_service', name="del-service"),
    url(r'^manage/services/edit/(?P<service_pk>\d+)?$', 'add_services', name="edit-services"),
    url(r'^manage/services/points/?$', 'get_service_points', name="get-service-points"),
    url(r'^manage/services/allpoints/?$', 'get_all_services', name="get-all-services"),

    url(r'^manage/servers/(?P<server_pk>\d+)?$', 'servers', name="servers"),
    url(r'^manage/servers/del/?$', 'del_server', name="del-server"),
    url(r'^manage/servers/edit/(?P<server_pk>\d+)?$', 'add_server', name="edit-servers"),

    url(r'^manage/realms/?$', 'realms', name="realms"),
    url(r'^manage/realms/edit/(?P<realm_pk>\d+)?$', 'add_realm', name="edit-realms"),
    url(r'^manage/realms/del/?$', 'del_realm', name="del-realm"),
    
    url(r'^manage/contacts/?$', 'contacts', name="contacts"),
    url(r'^manage/contacts/edit/(?P<contact_pk>\d+)?$', 'add_contact', name="edit-contacts"),
    url(r'^manage/contacts/del/?$', 'del_contact', name="del-contact"),

    url(r'^manage/adduser/?$', 'adduser', name="adduser"),
    

    

)

