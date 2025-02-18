from django.urls import path, re_path
import edumanage.views
from django.contrib.flatpages import views

urlpatterns = [
    re_path(r'^$', edumanage.views.index, name="index"),
    path("geolocate/", edumanage.views.geolocate, name="geolocate"),
    path("closest/", edumanage.views.closest, name="closest"),
    path("api/", edumanage.views.api, name="api"),
    path("world/", edumanage.views.world, name="world"),
    path("management/", edumanage.views.managementPage, name="managementPage"),
    path("worldpoints/", edumanage.views.worldPoints, name="worldPoints"),
    path("participants/", edumanage.views.participants, name="participants"),
    path("services/allpoints/", edumanage.views.get_all_services, name="get-all-services"),

    path("connect/", edumanage.views.connect, name="connect"),
    re_path(r'^cat-api(?:/(?P<cat_instance>[^/]+))?/?$', edumanage.views.cat_user_api_proxy, name="cat-api"),

    # eduroam db views
    re_path(r'^general(?:/v?(?P<version>[^/]+))?/institution.xml', edumanage.views.instxml, name="instxml"),
    re_path(r'^general(?:/v?(?P<version>[^/]+))?/(?P<resource>(realm|ro)).xml', edumanage.views.realmxml, name="realmxml"),
    path("usage/realm_data.xml", edumanage.views.realmdataxml, name="realmdataxml"),

    # The next two lines enable views that expose private/sensitive data:
    #url(r'^radius_serv_data', edumanage.views.servdata, name="servdata"),
    #url(r'^admin_mail_list', edumanage.views.adminlist, name="adminlist"),

    path("manage/", edumanage.views.manage, name="manage"),
    path("manage/login/", edumanage.views.manage_login_front, name="manage_login_front"),
    path("manage/selectinst/", edumanage.views.selectinst, name="selectinst"),

    path("manage/institutions/", edumanage.views.institutions, name="institutions"),
    re_path(r'^manage/institution/edit/(?P<institution_pk>\d+)/$', edumanage.views.add_institution_details, name="edit-institution"),
    re_path(r'^manage/services/(?P<service_pk>\d+)?$', edumanage.views.services, name="services"),
    path("manage/services/del/", edumanage.views.del_service, name="del-service"),
    re_path(r'^manage/services/edit/(?P<service_pk>\d+)?$', edumanage.views.add_services, name="edit-services"),
    path("manage/services/points/", edumanage.views.get_service_points, name="get-service-points"),
    re_path(r'^manage/servers/(?P<server_pk>\d+)?$', edumanage.views.servers, name="servers"),
    path("manage/servers/del/", edumanage.views.del_server, name="del-server"),
    re_path(r'^manage/servers/edit/(?P<server_pk>\d+)?$', edumanage.views.add_server, name="edit-servers"),
    path("manage/realms/", edumanage.views.realms, name="realms"),
    re_path(r'^manage/realms/edit/(?P<realm_pk>\d+)?$', edumanage.views.add_realm, name="edit-realms"),
    path("manage/realms/del/", edumanage.views.del_realm, name="del-realm"),
    path("manage/contacts/", edumanage.views.contacts, name="contacts"),
    re_path(r'^manage/contacts/edit/(?P<contact_pk>\d+)?$', edumanage.views.add_contact, name="edit-contacts"),
    path("manage/contacts/del/", edumanage.views.del_contact, name="del-contact"),
    path("manage/adduser/", edumanage.views.adduser, name="adduser"),
    path("manage/instrealmsmon/", edumanage.views.instrealmmon, name="instrealmmon"),
    re_path(r'^manage/instrealmsmon/edit/(?P<instrealmmon_pk>\d+)?$', edumanage.views.add_instrealmmon, name="edit-instrealmmon"),
    path("manage/instrealmsmon/del/", edumanage.views.del_instrealmmon, name="del-instrealmmon"),
    re_path(r'^manage/monlocauthpar/edit/(?P<instrealmmon_pk>\d+)/(?P<monlocauthpar_pk>\d+)?$', edumanage.views.add_monlocauthpar, name="edit-monlocauthpar"),
    path("manage/monlocauthpar/del/", edumanage.views.del_monlocauthpar, name="del-monlocauthpar"),
    path("manage/catenroll/", edumanage.views.cat_enroll, name="catenroll"),

    path("overview/", edumanage.views.overview, name="overview"),

    path("faq/el/", views.flatpage, {"url": "/faq/el/"}, name="faq-el"),
    path("faq/en/", views.flatpage, {"url": "/faq/en/"}, name="faq-en"),
    path("faq/mi/", views.flatpage, {"url": "/faq/mi/"}, name="faq-mi"),
    path("what/el/", views.flatpage, {"url": "/what/el/"}, name="what-el"),
    path("what/en/", views.flatpage, {"url": "/what/en/"}, name="what-en"),
]
