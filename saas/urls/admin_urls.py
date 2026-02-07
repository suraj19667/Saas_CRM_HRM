"""
StaffGrid SaaS Admin Dashboard URLs
Includes both existing admin views and new saas admin views
"""
from django.urls import path
from ..views.admin_dashboard_views import (
    admin_dashboard,
    subscription_list,
    subscription_plans_admin,
    one_time_plans_admin,
    custom_plans_admin,
    discount_list,
    discount_create,
    invoice_billing,
    admin_users,
)
from ..views.saas_admin_views import (
    manage_tenants,
    manage_plans,
    manage_subscriptions,
    manage_users,
    system_settings,
)

app_name = 'saas_admin'

urlpatterns = [
    # Main admin dashboard
    path('dashboard/', admin_dashboard, name='dashboard'),
    
    # Existing admin views
    path('subscription-list/', subscription_list, name='subscription_list'),
    path('subscription-plans/', subscription_plans_admin, name='subscription_plans'),
    path('one-time-plans/', one_time_plans_admin, name='one_time_plans'),
    path('custom-plans/', custom_plans_admin, name='custom_plans'),
    path('discounts/', discount_list, name='discount_list'),
    path('discounts/create/', discount_create, name='discount_create'),
    path('invoice-billing/', invoice_billing, name='invoice_billing'),
    path('admin-users/', admin_users, name='admin_users'),
    
    # New saas admin views
    path('tenants/', manage_tenants, name='tenants'),
    path('plans/', manage_plans, name='plans'),
    path('subscriptions/', manage_subscriptions, name='subscriptions'),
    path('users/', manage_users, name='users'),
    path('settings/', system_settings, name='settings'),
]




