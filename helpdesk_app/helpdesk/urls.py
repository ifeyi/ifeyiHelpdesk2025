from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.shortcuts import render
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _
from django.views.i18n import JavaScriptCatalog

schema_view = get_schema_view(
   openapi.Info(
      title="Helpdesk API",
      default_version='v1',
      description="API documentation for Helpdesk application",
      terms_of_service="https://www.example.com/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path(_('admin/'), admin.site.urls),
    path('', include('core.urls')),
    path(_('tickets/'), include('tickets.urls')),
    path(_('users/'), include('allauth.urls')),
    path(_('accounts/'), include('accounts.urls')),
    path(_('articles/'), include('articles.urls')),
    path(_('health/'), health_check, name='health_check'),
    path(_('metrics/'), include('django_prometheus.urls')),
    path(_('api/docs/'), schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(_('core/'), include('core.urls')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),  
    path(_('comments/'), include('comments.urls', namespace='comments')),
    prefix_default_language=True, 
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)