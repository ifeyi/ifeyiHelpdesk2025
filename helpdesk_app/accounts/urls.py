from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Basic URL patterns - implement the views as needed
    path('profile/', views.profile, name='account_profile'),
    path('agents/', views.agent_list, name='agent_list'),
    path('agents/<int:pk>/', views.agent_detail, name='agent_detail'),
    # Add more patterns as needed
    path('ldap/', views.ldap_login, name='ldap'),
]