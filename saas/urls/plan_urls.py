from django.urls import path
from ..views.plan_views import (
    plan_list, plan_create, plan_edit, plan_delete, public_plan_list,
    plan_features_manage, plan_feature_add, plan_feature_update, plan_feature_delete,
    one_time_plans, subscription_plans, custom_plans
)

app_name = 'plans'

urlpatterns = [
    path('', plan_list, name='plan_list'),
    path('one-time/', one_time_plans, name='one_time_plans'),
    path('subscription/', subscription_plans, name='subscription_plans'),
    path('custom/', custom_plans, name='custom_plans'),
    path('public/', public_plan_list, name='public_list'),
    path('create/', plan_create, name='plan_create'),
    path('<int:plan_id>/edit/', plan_edit, name='plan_edit'),
    path('<int:plan_id>/delete/', plan_delete, name='plan_delete'),
    path('<int:plan_id>/features/', plan_features_manage, name='plan_features_manage'),
    path('<int:plan_id>/features/add/', plan_feature_add, name='plan_feature_add'),
    path('<int:plan_id>/features/<int:plan_feature_id>/update/', plan_feature_update, name='plan_feature_update'),
    path('<int:plan_id>/features/<int:plan_feature_id>/delete/', plan_feature_delete, name='plan_feature_delete'),
]
