"""
SaaS Admin Dashboard URLs (for Super Admin only)
"""
from django.urls import path
from ..views.saas_admin_views import (
    saas_admin_dashboard,
    manage_tenants,
    manage_plans,
    manage_subscriptions,
    manage_users,
    system_settings,
)

app_name = 'saas_admin'

urlpatterns = [
    path('dashboard/', saas_admin_dashboard, name='dashboard'),
    path('tenants/', manage_tenants, name='tenants'),
    path('plans/', manage_plans, name='plans'),
    path('subscriptions/', manage_subscriptions, name='subscriptions'),
    path('users/', manage_users, name='users'),
    path('settings/', system_settings, name='settings'),
]
