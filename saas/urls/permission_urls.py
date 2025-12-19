"""
URL configuration for permission management views.

Routes:
- /permissions/ → List all permissions
- /permissions/add/ → Add new permission
- /permissions/<id>/edit/ → Edit permission
- /permissions/<id>/delete/ → Delete permission
"""

from django.urls import path
from ..views.permission_views import (
    permissions_list,
    add_permission,
    edit_permission,
    delete_permission,
)

app_name = 'permissions'

urlpatterns = [
    # List permissions
    path('', permissions_list, name='permissions_list'),
    
    # Add new permission
    path('add/', add_permission, name='add_permission'),
    
    # Edit permission
    path('<int:permission_id>/edit/', edit_permission, name='edit_permission'),
    
    # Delete permission
    path('<int:permission_id>/delete/', delete_permission, name='delete_permission'),
]
