from django.urls import path
from ..api_views import (
    api_subscription_plans_list,
    api_subscription_plan_detail,
)

urlpatterns = [
    path('', api_subscription_plans_list, name='api_subscription_plans_list'),
    path('<int:plan_id>/', api_subscription_plan_detail, name='api_subscription_plan_detail'),
]
