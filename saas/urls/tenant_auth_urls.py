from django.urls import path
from ..views.company_auth_views import company_login_view

app_name = 'tenant_auth'

urlpatterns = [
    path('<str:tenant_domain>/login/', company_login_view, name='login'),
]