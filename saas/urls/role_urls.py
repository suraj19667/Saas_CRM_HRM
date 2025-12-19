from django.urls import path
from ..views.role_views import roles_list, add_role, edit_role, delete_role

app_name = 'roles'

urlpatterns = [
    path('', roles_list, name='roles_list'),
    path('add/', add_role, name='add_role'),
    path('<int:role_id>/edit/', edit_role, name='edit_role'),
    path('<int:role_id>/delete/', delete_role, name='delete_role'),]