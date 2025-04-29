from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('add/<str:model_name>/<int:object_id>/', views.add_comment, name='add-comment'),
    path('delete/<int:pk>/', views.delete_comment, name='delete-comment'),
]