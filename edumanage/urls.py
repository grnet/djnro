from django.conf.urls import patterns, url
import edumanage.views

urlpatterns = patterns(
    'edumanage.views',
    url(r'^$', edumanage.views.index, name="index"),
    url(r'^geolocate/?$', edumanage.views.geolocate, name="geolocate"),
    url(r'^closest/?$', edumanage.views.closest, name="closest"),
    url(r'^api/?$', edumanage.views.api, name="api"),
    url(r'^world/?$', edumanage.views.world, name="world"),
    url(r'^management/?$', edumanage.views.managementPage, name="managementPage"),
    url(r'^worldpoints/?$', edumanage.views.worldPoints, name="worldPoints"),
    url(r'^participants/?$', edumanage.views.participants, name="participants"),
    url(r'^services/allpoints/?$', edumanage.views.get_all_services, name="get-all-services"),

    url(r'^connect/?$', edumanage.views.connect, name="connect"),
    url(r'^cat-api(?:/(?P<cat_instance>[^/]+))?/?$', edumanage.views.cat_user_api_proxy, name="cat-api"),

    # eduroam db views
    url(r'^general/institution.xml', edumanage.views.instxml, name="instxml"),
    url(r'^general/realm.xml', edumanage.views.realmxml, name="realmxml"),
    url(r'^usage/realm_data.xml', edumanage.views.realmdataxml, name="realmdataxml"),

    # The next two lines enable views that expose private/sensitive data:
    #url(r'^radius_serv_data', edumanage.views.servdata, name="servdata"),
    #url(r'^admin_mail_list', edumanage.views.adminlist, name="adminlist"),

    url(r'^manage/$', edumanage.views.manage, name="manage"),
    url(r'^manage/login/$', edumanage.views.manage_login_front, name="manage_login_front"),
    url(r'^manage/selectinst/$', edumanage.views.selectinst, name="selectinst"),

    url(r'^manage/institutions/$', edumanage.views.institutions, name="institutions"),
    url(r'^manage/institution/edit/(?P<institution_pk>\d+)/$', edumanage.views.add_institution_details, name="edit-institution"),
    url(r'^manage/services/(?P<service_pk>\d+)?$', edumanage.views.services, name="services"),
    url(r'^manage/services/del/$', edumanage.views.del_service, name="del-service"),
    url(r'^manage/services/edit/(?P<service_pk>\d+)?$', edumanage.views.add_services, name="edit-services"),
    url(r'^manage/services/points/?$', edumanage.views.get_service_points, name="get-service-points"),
    url(r'^manage/servers/(?P<server_pk>\d+)?$', edumanage.views.servers, name="servers"),
    url(r'^manage/servers/del/?$', edumanage.views.del_server, name="del-server"),
    url(r'^manage/servers/edit/(?P<server_pk>\d+)?$', edumanage.views.add_server, name="edit-servers"),
    url(r'^manage/realms/?$', edumanage.views.realms, name="realms"),
    url(r'^manage/realms/edit/(?P<realm_pk>\d+)?$', edumanage.views.add_realm, name="edit-realms"),
    url(r'^manage/realms/del/?$', edumanage.views.del_realm, name="del-realm"),
    url(r'^manage/contacts/?$', edumanage.views.contacts, name="contacts"),
    url(r'^manage/contacts/edit/(?P<contact_pk>\d+)?$', edumanage.views.add_contact, name="edit-contacts"),
    url(r'^manage/contacts/del/?$', edumanage.views.del_contact, name="del-contact"),
    url(r'^manage/adduser/?$', edumanage.views.adduser, name="adduser"),
    url(r'^manage/instrealmsmon/?$', edumanage.views.instrealmmon, name="instrealmmon"),
    url(r'^manage/instrealmsmon/edit/(?P<instrealmmon_pk>\d+)?$', edumanage.views.add_instrealmmon, name="edit-instrealmmon"),
    url(r'^manage/instrealmsmon/del/?$', edumanage.views.del_instrealmmon, name="del-instrealmmon"),
    url(r'^manage/monlocauthpar/edit/(?P<instrealmmon_pk>\d+)/(?P<monlocauthpar_pk>\d+)?$', edumanage.views.add_monlocauthpar, name="edit-monlocauthpar"),
    url(r'^manage/monlocauthpar/del/?$', edumanage.views.del_monlocauthpar, name="del-monlocauthpar"),
    url(r'^manage/catenroll/?$', edumanage.views.cat_enroll, name="catenroll"),

    url(r'^overview/?$', edumanage.views.overview, name="overview"),
)
