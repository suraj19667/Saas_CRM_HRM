from django.urls import path
from ..views.tenant_dashboard_views import tenant_dashboard

app_name = 'tenant'

urlpatterns = [
    path('<slug:tenant_slug>/dashboard/', tenant_dashboard, name='tenant_dashboard'),
]