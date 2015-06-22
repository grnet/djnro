from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
# Uncomment the next two lines to enable the django admin interface:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^accounts/', include('social.apps.django_app.urls', namespace='social')),
    (r'^setlang/?$', 'django.views.i18n.set_language'),
    (r'^admin/', include(admin.site.urls)),
    url(r'^managelogin/(?P<backend>[^/]+)/$', 'edumanage.views.manage_login', name='manage_login'),
    url(r'^login/?', 'edumanage.views.user_login', name="login"),
    url(r'^altlogin/?', 'django.contrib.auth.views.login', {'template_name': 'overview/login.html'}, name="altlogin"),
    url(r'^logout/?', 'django.contrib.auth.views.logout', {'next_page': '/'}, name="logout"),
    url(r'^registration/accounts/activate/(?P<activation_key>\w+)/$', 'accounts.views.activate', name='activate_account'),
    url(
        r'^registration/activate/complete/$',
        direct_to_template,
        {'template': 'registration/activation_complete.html'},
        name='registration_activation_complete'
    ),
    (r'^tinymce/', include('tinymce.urls')),
    url(r'^', include('edumanage.urls')),
)
