from django.urls import path, re_path
import edumanage.views
from django.contrib.flatpages import views

urlpatterns = [
    path('', edumanage.views.index, name="index"),
    path("geolocate/", edumanage.views.geolocate, name="geolocate"),
    path("closest/", edumanage.views.closest, name="closest"),
    path("api/", edumanage.views.api, name="api"),
    path("world/", edumanage.views.world, name="world"),
    path("management/", edumanage.views.managementPage, name="managementPage"),
    path("worldpoints/", edumanage.views.worldPoints, name="worldPoints"),
    path("participants/", edumanage.views.participants, name="participants"),
    path("services/allpoints/", edumanage.views.get_all_services, name="get-all-services"),

    path("connect/", edumanage.views.connect, name="connect"),
    path("cat-api/", edumanage.views.cat_user_api_proxy, name="cat-api"),
    path("cat-api/<str:cat_instance>/", edumanage.views.cat_user_api_proxy, name="cat-api"),

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
    path('manage/institution/edit/<int:institution_pk>/', edumanage.views.add_institution_details, name="edit-institution"),
    path("manage/services/", edumanage.views.services, name="services"),
    path("manage/services/<int:service_pk>/", edumanage.views.services, name="services"),
    path("manage/services/del/", edumanage.views.del_service, name="del-service"),
    path("manage/services/edit/<int:service_pk>/", edumanage.views.add_services, name="edit-services"),
    path("manage/services/edit/", edumanage.views.add_services, name="edit-services"),
    path("manage/services/points/", edumanage.views.get_service_points, name="get-service-points"),
    path("manage/servers/", edumanage.views.servers, name="servers"),
    path("manage/servers/<int:server_pk>/", edumanage.views.servers, name="servers"),
    path("manage/servers/del/", edumanage.views.del_server, name="del-server"),
    path("manage/servers/edit/<int:server_pk>/", edumanage.views.add_server, name="edit-servers"),
    path("manage/servers/edit/", edumanage.views.add_server, name="edit-servers"),
    path("manage/realms/", edumanage.views.realms, name="realms"),
    path("manage/realms/edit/<int:realm_pk>", edumanage.views.add_realm, name="edit-realms"),
    path("manage/realms/edit/", edumanage.views.add_realm, name="edit-realms"),
    path("manage/realms/del/", edumanage.views.del_realm, name="del-realm"),
    path("manage/contacts/", edumanage.views.contacts, name="contacts"),
    path("manage/contacts/edit/<int:contact_pk>/", edumanage.views.add_contact, name="edit-contacts"),
    path("manage/contacts/edit/", edumanage.views.add_contact, name="edit-contacts"),
    path("manage/contacts/del/", edumanage.views.del_contact, name="del-contact"),
    path("manage/adduser/", edumanage.views.adduser, name="adduser"),
    path("manage/instrealmsmon/", edumanage.views.instrealmmon, name="instrealmmon"),
    path("manage/instrealmsmon/edit/<int:instrealmmon_pk>/", edumanage.views.add_instrealmmon, name="edit-instrealmmon"),
    path("manage/instrealmsmon/edit/", edumanage.views.add_instrealmmon, name="edit-instrealmmon"),
    path("manage/instrealmsmon/del/", edumanage.views.del_instrealmmon, name="del-instrealmmon"),
    path("manage/monlocauthpar/edit/<int:instrealmmon_pk>/<int:monlocauthpar_pk>/", edumanage.views.add_monlocauthpar, name="edit-monlocauthpar"),
    path("manage/monlocauthpar/edit/<int:instrealmmon_pk>/", edumanage.views.add_monlocauthpar, name="edit-monlocauthpar"),
    path("manage/monlocauthpar/del/", edumanage.views.del_monlocauthpar, name="del-monlocauthpar"),
    path("manage/catenroll/", edumanage.views.cat_enroll, name="catenroll"),

    path("overview/", edumanage.views.overview, name="overview"),

    path("faq/el/", views.flatpage, {"url": "/faq/el/"}, name="faq-el"),
    path("faq/en/", views.flatpage, {"url": "/faq/en/"}, name="faq-en"),
    path("faq/mi/", views.flatpage, {"url": "/faq/mi/"}, name="faq-mi"),
    path("what/el/", views.flatpage, {"url": "/what/el/"}, name="what-el"),
    path("what/en/", views.flatpage, {"url": "/what/en/"}, name="what-en"),
]
