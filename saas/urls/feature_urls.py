from django.urls import path
from ..views.feature_views import feature_list, feature_create, feature_edit, feature_delete

app_name = 'features'

urlpatterns = [
    path('', feature_list, name='feature_list'),
    path('create/', feature_create, name='feature_create'),
    path('<int:feature_id>/edit/', feature_edit, name='feature_edit'),
    path('<int:feature_id>/delete/', feature_delete, name='feature_delete'),
]
