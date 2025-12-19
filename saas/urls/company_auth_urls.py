from django.urls import path
from ..views.company_auth_views import (
    company_register_view,
    company_login_view,
    subscription_plans_view,
    create_razorpay_order,
    payment_success,
    payment_cancel,
    update_tenant_info
)

app_name = 'company'

urlpatterns = [
    path('register/', company_register_view, name='register'),
    path('login/', company_login_view, name='login'),
    path('subscriptions/', subscription_plans_view, name='subscription_plans'),
    path('update-tenant-info/', update_tenant_info, name='update_tenant_info'),
    path('create-order/<int:plan_id>/', create_razorpay_order, name='create_razorpay_order'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),
]