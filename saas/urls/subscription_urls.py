
from django.urls import path
from ..views.subscription_views import (
    list_plans,
    subscribe_plan,
    cancel_subscription,
    process_payment,
    payment_success,
)

app_name = 'subscription'

urlpatterns = [
    path('', list_plans, name='list_plans'),
    path('<int:plan_id>/subscribe/', subscribe_plan, name='subscribe_plan'),
    path('<int:plan_id>/payment/', process_payment, name='process_payment'),
    path('<int:subscription_id>/success/', payment_success, name='payment_success'),
    path('<int:subscription_id>/cancel/', cancel_subscription, name='cancel_subscription'),
]
