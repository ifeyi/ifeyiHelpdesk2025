from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('ldap/', views.ldap_login, name='ldap'),
]