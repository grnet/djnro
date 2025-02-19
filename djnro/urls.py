from django.urls import include
from django.urls import path
# Uncomment the next two lines to enable the django admin interface:
from django.contrib import admin
admin.autodiscover()
import social_django.urls
from edumanage import views as edumanage_views
import django
import accounts, accounts.views
from django_registration.backends.activation.views import ActivationView

urlpatterns = [
    path("accounts/", include(social_django.urls, namespace='social')),
    path("setlang/", django.views.i18n.set_language, name='set_language'),
    path("admin/", admin.site.urls),
    path('managelogin/<str:backend>/', edumanage_views.manage_login, name='manage_login'),
    path("login/", edumanage_views.user_login, name="login"),
    path("altlogin/", django.contrib.auth.views.LoginView.as_view(template_name='overview/login.html'), name="altlogin"),
    path("logout/", edumanage_views.user_logout, {'next_page': '/'}, name="logout"),
    path('registration/accounts/activate/<path:activation_key>/', accounts.views.activate, name='activate_account'),
    path(
        "registration/activate/complete/",
        ActivationView.as_view(template_name='registration/activation_complete.html'),
        name='registration_activation_complete'
    ),
    path("tinymce/", include('tinymce.urls')),
    path('', include('edumanage.urls')),
]
