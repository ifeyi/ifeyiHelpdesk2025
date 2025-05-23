from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tickets'
router = DefaultRouter()

urlpatterns = [
    path('', views.ticket_list, name='ticket-list'),
    path('<int:pk>/', views.ticket_detail, name='ticket-detail'),
    path('create/', views.ticket_create, name='ticket-create'),
    path('<int:pk>/update/', views.ticket_update, name='ticket-update'),
    path('<int:pk>/delete/', views.ticket_delete, name='ticket-delete'),
    path('<int:pk>/change-status/', views.ticket_change_status, name='ticket-change-status'),
    path('<int:pk>/assign/', views.ticket_assign, name='ticket-assign'),
    path('<int:pk>/auto-assign/', views.ticket_auto_assign, name='ticket-auto-assign'),
    path('api/subcategories/<int:parent_id>/', views.get_subcategories, name='get-subcategories'),
    path('api/subdepartments/<int:department_id>/', views.get_subdepartments, name='get-subdepartments'),
]

urlpatterns += router.urls