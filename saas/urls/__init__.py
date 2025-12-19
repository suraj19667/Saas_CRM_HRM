from django.urls import path, include
from ..views import login_view, register_view, verify_otp_view, resend_otp_view, logout_view, deshboard_view, leads_view, deals_view, form_builder_view, contract_view, crm_setup_view, users_list, admin_dashboard_view
from ..views.hrm_views import hrm_home
from ..views.access_management_views import access_management
from ..api_views import (
    api_roles_list, api_role_detail,
    api_permissions_list,
    api_users_list, api_user_create, api_user_update, api_user_delete,
    api_me
)
from ..api_feature_views import (
    get_feature, create_feature, update_feature, delete_feature, list_features
)

urlpatterns = [
    path('', login_view, name='home'),
    path('auth/', include('saas.urls.auth_urls', namespace='auth')),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('logout/', logout_view, name='logout'),
    path('login/', login_view, name='login'),  # Login
    path('register/', register_view, name='register'),  # Register
    # Compatibility route for legacy references
    path('dashboard/', deshboard_view, name='dashboard'),
    # SaaS admin dashboard (also available under /saas/)
    path('saas/dashboard/', deshboard_view, name='saas_dashboard'),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('leads/', leads_view, name='leads'),
    path('deals/', deals_view, name='deals'),
    path('form-builder/', form_builder_view, name='form_builder'),
    path('contract/', contract_view, name='contract'),
    path('crm-setup/', crm_setup_view, name='crm_setup'),
    path('users/', users_list, name='users'),
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
    # Feature API endpoints
    path('api/features/', list_features, name='api_features_list'),
    path('api/features/create/', create_feature, name='api_feature_create'),
    path('api/features/<int:feature_id>/', get_feature, name='api_feature_detail'),
    path('api/features/<int:feature_id>/update/', update_feature, name='api_feature_update'),
    path('api/features/<int:feature_id>/delete/', delete_feature, name='api_feature_delete'),
    # path('api/subscriptions/', include('saas.urls.subscription_api_urls')),
    path('payment/', include('saas.urls.payment_urls')),
    # path('dashboard/', include('saas.urls.dashboard_urls')),
    path('plans/', include('saas.urls.plan_urls', namespace='plans')),
    path('features/', include('saas.urls.feature_urls', namespace='features')),
    path('addons/', include('saas.urls.addon_urls')),
    # path('subscriptions/', include('saas.urls.subscription_urls')),
    # Tenant management and tenant dashboard namespace
    path('tenant/', include('saas.urls.tenant_urls')),
    path('tenant/', include('saas.urls.tenant_dashboard_urls', namespace='tenant_dashboard')),
    # HRM home (simple landing for HRM dashboard)
    path('hrm/', hrm_home, name='hrm_home'),
]