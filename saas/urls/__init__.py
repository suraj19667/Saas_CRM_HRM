from django.urls import path, include
from ..views import login_view, register_view, verify_otp_view, resend_otp_view, logout_view, leads_view, deals_view, form_builder_view, contract_view, crm_setup_view, users_list, user_edit, user_delete
from ..views.dashboard_views import (
    user_detail, 
    staffgrid_dashboard_overview, 
    staffgrid_tenants, 
    staffgrid_plans, 
    staffgrid_subscriptions
)
from ..views.hrm_views import (
    hrm_home, 
    hrm_overview, 
    hrm_my_plan, 
    hrm_usage, 
    hrm_addons, 
    hrm_billing, 
    hrm_payment_methods,
    hrm_account_settings,
    hrm_support,
    hrm_plans
)
from ..views.access_management_views import access_management
from ..views.new_dashboard_views import (
    landing_view,
    profile_view, 
    forgot_password_view, 
    change_password_view
)
from ..api_views import (
    api_roles_list, api_role_detail,
    api_permissions_list,
    api_users_list, api_user_create, api_user_update, api_user_delete,
    api_me
)
from ..api_dashboard_views import (
    api_dashboard_stats, api_dashboard_revenue, api_dashboard_plan_distribution,
    api_tenants_list, api_plans_list, api_subscriptions_list
)
from ..api_feature_views import (
    get_feature, create_feature, update_feature, delete_feature, list_features
)

urlpatterns = [
    # Root shows landing page (public)
    path('', landing_view, name='home'),
    path('landing/', landing_view, name='landing'),
    
    # Authentication URLs
    path('auth/', include('saas.urls.auth_urls', namespace='auth')),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('logout/', logout_view, name='logout'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('change-password/', change_password_view, name='change_password'),
    
    # StaffGrid Dashboard URLs (ONLY DASHBOARD)
    path('dashboard/', staffgrid_dashboard_overview, name='dashboard'),
    path('dashboard/overview/', staffgrid_dashboard_overview, name='dashboard_overview'),
    path('dashboard/tenants/', staffgrid_tenants, name='dashboard_tenants'),
    path('dashboard/plans/', staffgrid_plans, name='dashboard_plans'),
    path('dashboard/subscriptions/', staffgrid_subscriptions, name='dashboard_subscriptions'),
    
    # Profile
    path('profile/', profile_view, name='profile'),
    
    # CRM URLs
    path('leads/', leads_view, name='leads'),
    path('deals/', deals_view, name='deals'),
    path('form-builder/', form_builder_view, name='form_builder'),
    path('contract/', contract_view, name='contract'),
    path('crm-setup/', crm_setup_view, name='crm_setup'),
    path('users/', users_list, name='users_list'),
    path('users/admin/', users_list, name='admin_user'),
    path('users/<int:user_id>/', user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', user_delete, name='user_delete'),
    path('access-management/', access_management, name='access_management'),
    path('roles-permissions/', include('saas.urls.access_control_urls')),
    path('roles/', include('saas.urls.role_urls')),
    path('permissions/', include('saas.urls.permission_urls')),
    path('subscriptions/', include('saas.urls.subscription_urls')),
    path('tenant/', include('saas.urls.tenant_urls', namespace='tenant_mgmt')),
    # API Endpoints
    path('api/roles/', api_roles_list, name='api_roles_list'),
    path('api/roles/<int:role_id>/', api_role_detail, name='api_role_detail'),
    path('api/permissions/', api_permissions_list, name='api_permissions_list'),
    path('api/users/', api_users_list, name='api_users_list'),
    path('api/users/create/', api_user_create, name='api_user_create'),
    path('api/users/<int:user_id>/update/', api_user_update, name='api_user_update'),
    path('api/users/<int:user_id>/delete/', api_user_delete, name='api_user_delete'),
    path('api/me/', api_me, name='api_me'),
    
    # StaffGrid Dashboard API Endpoints
    path('api/dashboard/stats/', api_dashboard_stats, name='api_dashboard_stats'),
    path('api/dashboard/revenue/', api_dashboard_revenue, name='api_dashboard_revenue'),
    path('api/dashboard/plan-distribution/', api_dashboard_plan_distribution, name='api_dashboard_plan_distribution'),
    path('api/tenants/', api_tenants_list, name='api_tenants_list'),
    path('api/plans/', api_plans_list, name='api_plans_list'),
    path('api/subscriptions/', api_subscriptions_list, name='api_subscriptions_list'),
    
    # Feature API endpoints
    path('api/features/', list_features, name='api_features_list'),
    path('api/features/create/', create_feature, name='api_feature_create'),
    path('api/features/<int:feature_id>/', get_feature, name='api_feature_detail'),
    path('api/features/<int:feature_id>/update/', update_feature, name='api_feature_update'),
    path('api/features/<int:feature_id>/delete/', delete_feature, name='api_feature_delete'),
    # path('api/subscriptions/', include('saas.urls.subscription_api_urls')),
    path('payment/', include('saas.urls.payment_urls')),
    # SaaS admin URLs (namespaced as 'saas_admin')
    path('saas-admin/', include('saas.urls.admin_urls', namespace='saas_admin')),
    # path('dashboard/', include('saas.urls.dashboard_urls')),
    path('plans/', include('saas.urls.plan_urls', namespace='plans')),
    path('features/', include('saas.urls.feature_urls', namespace='features')),
    path('addons/', include('saas.urls.addon_urls')),
    # path('subscriptions/', include('saas.urls.subscription_urls')),
    # Tenant management and tenant dashboard namespace
    path('tenant/', include('saas.urls.tenant_urls')),
    path('tenant/', include('saas.urls.tenant_dashboard_urls', namespace='tenant_dashboard')),
    # HRM Dashboard URLs (complete SaaS HRM system)
    path('hrm/', hrm_home, name='hrm_home'),
    path('hrm/overview/', hrm_overview, name='hrm_overview'),
    path('hrm/my-plan/', hrm_my_plan, name='hrm_my_plan'),
    path('hrm/usage/', hrm_usage, name='hrm_usage'),
    path('hrm/addons/', hrm_addons, name='hrm_addons'),
    path('hrm/billing/', hrm_billing, name='hrm_billing'),
    path('hrm/payment-methods/', hrm_payment_methods, name='hrm_payment_methods'),
    path('hrm/account-settings/', hrm_account_settings, name='hrm_account_settings'),
    path('hrm/support/', hrm_support, name='hrm_support'),
    path('hrm/plans/', hrm_plans, name='hrm_plans'),
]