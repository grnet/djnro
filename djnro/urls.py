from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template
# Uncomment the next two lines to enable the django admin interface:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/', include('social_auth.urls')),
    (r'^setlang/?$', 'django.views.i18n.set_language'),
    # Uncomment the next line to enable django admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    url(r'^managelogin/(?P<backend>[^/]+)/$', 'edumanage.views.manage_login', name='manage_login'),
    url(r'^login/?', 'edumanage.views.user_login', name="login"),
    url(r'^altlogin/?', 'django.contrib.auth.views.login', {'template_name': 'overview/login.html'}, name="altlogin"),
    url(r'^logout/?', 'django.contrib.auth.views.logout', {'next_page': '/'}, name="logout"),
    url(r'^registration/accounts/activate/(?P<activation_key>\w+)/$', 'accounts.views.activate', name='activate_account'),
    url(r'^registration/activate/complete/$',
                           direct_to_template,
                           { 'template': 'registration/activation_complete.html' },
                           name='registration_activation_complete'),
    (r'^tinymce/', include('tinymce.urls')),
)

urlpatterns += patterns('edumanage.views',
    url(r'^$', 'index', name="index"),
    url(r'^geolocate/?$', 'geolocate', name="geolocate"),
    url(r'^closest/?$', 'closest', name="closest"),
    url(r'^api/?$', 'api', name="api"),
    url(r'^world/?$', 'world', name="world"),
    url(r'^management/?$', 'managementPage', name="managementPage"),
    url(r'^worldpoints/?$', 'worldPoints', name="worldPoints"),
    url(r'^participants/?$', 'participants', name="participants"),
    url(r'^services/allpoints/?$', 'get_all_services', name="get-all-services"),

    url(r'^general/institution.xml', "instxml", name="instxml"),
    url(r'^general/realm.xml', "realmxml", name="realmxml"),
    url(r'^usage/realm_data.xml', "realmdataxml", name="realmdataxml"),

    # The next two lines enable views that expose private/sensitive data:
    #url(r'^radius_serv_data', "servdata", name="servdata"),
    #url(r'^admin_mail_list', "adminlist", name="adminlist"),

    url(r'^manage/?$', 'manage', name="manage"),
    url(r'^manage/login/?$', 'manage_login_front', name="manage_login_front"),
    url(r'^manage/selectinst/?$', 'selectinst', name="selectinst"),

    url(r'^manage/institutions/?$', 'institutions', name="institutions"),
    url(r'^manage/institution/edit/(?P<institution_pk>\d+)?$', 'add_institution_details', name="edit-institution"),
    url(r'^manage/services/(?P<service_pk>\d+)?$', 'services', name="services"),
    url(r'^manage/services/del/?$', 'del_service', name="del-service"),
    url(r'^manage/services/edit/(?P<service_pk>\d+)?$', 'add_services', name="edit-services"),
    url(r'^manage/services/points/?$', 'get_service_points', name="get-service-points"),
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
    url(r'^manage/instrealmsmon/?$', 'instrealmmon', name="instrealmmon"),
    url(r'^manage/instrealmsmon/edit/(?P<instrealmmon_pk>\d+)?$', 'add_instrealmmon', name="edit-instrealmmon"),
    url(r'^manage/instrealmsmon/del/?$', 'del_instrealmmon', name="del-instrealmmon"),
    url(r'^manage/monlocauthpar/edit/(?P<instrealmmon_pk>\d+)/(?P<monlocauthpar_pk>\d+)?$', 'add_monlocauthpar', name="edit-monlocauthpar"),
    url(r'^manage/monlocauthpar/del/?$', 'del_monlocauthpar', name="del-monlocauthpar"),
    url(r'^manage/catenroll/?$', 'cat_enroll', name="catenroll"),

    url(r'^overview/?$', 'overview', name="overview"),
)

# if settings.DEBUG:
#     urlpatterns += patterns('',
#         (r'^static/(?P<path>.*)', 'django.views.static.serve',\
#             {'document_root':  settings.STATIC_URL}),
#     )
