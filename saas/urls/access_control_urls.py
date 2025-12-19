"""
URL configuration for unified Access Control management (Roles and Permissions).
"""

from django.urls import path
from ..views.access_control_views import (
    access_control_dashboard,
    roles_and_permissions_list,
    role_detail,
    permission_detail,
    manage_role_permissions,
    create_role,
    edit_role,
    delete_role,
    create_permission,
    edit_permission,
    delete_permission,
)

app_name = 'access_control'

urlpatterns = [
    # Dashboard
    path('', access_control_dashboard, name='dashboard'),
    
    # Unified list view
    path('roles-and-permissions/', roles_and_permissions_list, name='roles_and_permissions_list'),
    
    # Role management
    path('roles/create/', create_role, name='create_role'),
    path('roles/<int:role_id>/', role_detail, name='role_detail'),
    path('roles/<int:role_id>/edit/', edit_role, name='edit_role'),
    path('roles/<int:role_id>/delete/', delete_role, name='delete_role'),
    path('roles/<int:role_id>/manage-permissions/', manage_role_permissions, name='manage_role_permissions'),
    
    # Permission management
    path('permissions/create/', create_permission, name='create_permission'),
    path('permissions/<int:permission_id>/', permission_detail, name='permission_detail'),
    path('permissions/<int:permission_id>/edit/', edit_permission, name='edit_permission'),
    path('permissions/<int:permission_id>/delete/', delete_permission, name='delete_permission'),
]
