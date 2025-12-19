from django.urls import path
from ..views.addon_views import (
    addon_list_view,
    addon_create_view,
    addon_edit_view,
    addon_delete_view,
    addon_toggle_status_view
)

urlpatterns = [
    path('', addon_list_view, name='addon_list'),
    path('create/', addon_create_view, name='addon_create'),
    path('<int:addon_id>/edit/', addon_edit_view, name='addon_edit'),
    path('<int:addon_id>/delete/', addon_delete_view, name='addon_delete'),
    path('<int:addon_id>/toggle-status/', addon_toggle_status_view, name='addon_toggle_status'),
]
