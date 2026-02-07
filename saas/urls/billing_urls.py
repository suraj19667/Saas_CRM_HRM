"""
Billing and Pricing URLs
"""
from django.urls import path
from ..views.billing_views import (
    pricing_page,
    select_plan,
    checkout,
    payment_success,
    payment_failed
)

app_name = 'billing'

urlpatterns = [
    path('pricing/', pricing_page, name='pricing'),
    path('select-plan/<int:plan_id>/', select_plan, name='select_plan'),
    path('checkout/<int:plan_id>/', checkout, name='checkout'),
    path('payment-success/', payment_success, name='payment_success'),
    path('payment-failed/', payment_failed, name='payment_failed'),
]
