from django.conf.urls import include
from django.urls import path, re_path
# Uncomment the next two lines to enable the django admin interface:
from django.contrib import admin
admin.autodiscover()
import social_django.urls
import edumanage
import django
import accounts, accounts.views
from django_registration.backends.activation.views import ActivationView

urlpatterns = [
    path("accounts/", include(social_django.urls, namespace='social')),
    path("setlang/", edumanage.views.set_language, name='set_language'),
    path("admin/", admin.site.urls),
    re_path(r'^managelogin/(?P<backend>[^/]+)/$', edumanage.views.manage_login, name='manage_login'),
    path("login/", edumanage.views.user_login, name="login"),
    path("altlogin/", django.contrib.auth.views.LoginView.as_view(template_name='overview/login.html'), name="altlogin"),
    path("logout/", edumanage.views.user_logout, {'next_page': '/'}, name="logout"),
    re_path(r'^registration/accounts/activate/(?P<activation_key>.+)/$', accounts.views.activate, name='activate_account'),
    path(
        "registration/activate/complete/",
        ActivationView.as_view(template_name='registration/activation_complete.html'),
        name='registration_activation_complete'
    ),
    path("tinymce/", include('tinymce.urls')),
    re_path(r'^', include('edumanage.urls')),
]
