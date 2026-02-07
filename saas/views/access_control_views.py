"""
Unified Access Control Views for Roles and Permissions Management.
Provides comprehensive management interface for both roles and permissions.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model

from ..models import Role, Permission, RolePermission
from ..forms import RoleForm, PermissionForm

User = get_user_model()


@login_required(login_url='auth:login')
def access_control_dashboard(request):
    """
    Unified dashboard for managing roles and permissions.
    Displays comprehensive statistics and quick action options.
    """
    # Get statistics
    roles_count = Role.objects.count()
    permissions_count = Permission.objects.count()
    
    # Get recent roles
    roles = Role.objects.all()[:5]
    
    # Get recent permissions
    permissions = Permission.objects.all()[:5]
    
    context = {
        'roles_count': roles_count,
        'permissions_count': permissions_count,
        'roles': roles,
        'permissions': permissions,
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/dashboard.html', context)


@login_required(login_url='auth:login')
def roles_and_permissions_list(request):
    """
    Unified list view for roles and permissions with tabs.
    """
    tab = request.GET.get('tab', 'roles')
    page_num = request.GET.get('page', 1)
    
    context = {
        'current_section': 'roles_permissions',
        'tab': tab,
    }
    
    if tab == 'roles':
        # Get roles with pagination
        roles_queryset = Role.objects.order_by('-created_at')
        
        paginator = Paginator(roles_queryset, 10)
        try:
            page = paginator.page(page_num)
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
        
        context['roles'] = page.object_list
        context['page_obj'] = page
        context['paginator'] = paginator
        
    elif tab == 'permissions':
        # Get permissions with pagination
        permissions_queryset = Permission.objects.order_by('-created_at')
        
        paginator = Paginator(permissions_queryset, 10)
        try:
            page = paginator.page(page_num)
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
        
        context['permissions'] = page.object_list
        context['page_obj'] = page
        context['paginator'] = paginator
    
    return render(request, 'access_control/roles_and_permissions_list.html', context)


@login_required(login_url='auth:login')
def role_detail(request, role_id):
    """
    View detailed information about a specific role and manage its permissions.
    """
    role = get_object_or_404(Role, id=role_id)
    
    # Get all available permissions
    all_permissions = Permission.objects.all()
    
    # Get permissions assigned to this role
    assigned_permission_ids = RolePermission.objects.filter(
        role=role
    ).values_list('permission_id', flat=True)
    
    if request.method == 'POST':
        # Update role permissions
        permission_ids = request.POST.getlist('permissions')
        
        # Clear existing permissions
        RolePermission.objects.filter(role=role).delete()
        
        # Add new permissions
        for perm_id in permission_ids:
            try:
                permission = Permission.objects.get(id=perm_id)
                RolePermission.objects.create(role=role, permission=permission)
            except Permission.DoesNotExist:
                continue
        
        messages.success(request, f'Permissions updated for role "{role.name}"')
        return redirect('access_control:role_detail', role_id=role.id)
    
    context = {
        'role': role,
        'all_permissions': all_permissions,
        'assigned_permission_ids': list(assigned_permission_ids),
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/role_detail.html', context)


@login_required(login_url='auth:login')
def permission_detail(request, permission_id):
    """
    View detailed information about a specific permission and which roles have it.
    """
    permission = get_object_or_404(Permission, id=permission_id)
    
    # Get roles that have this permission
    roles_with_permission = Role.objects.filter(
        role_permissions__permission=permission
    )
    
    context = {
        'permission': permission,
        'roles_with_permission': roles_with_permission,
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/permission_detail.html', context)


@login_required(login_url='auth:login')
def manage_role_permissions(request, role_id):
    """
    Manage permissions for a specific role via modal/form.
    """
    role = get_object_or_404(Role, id=role_id)
    all_permissions = Permission.objects.all()
    
    if request.method == 'POST':
        permission_ids = request.POST.getlist('permissions')
        
        # Clear existing permissions
        RolePermission.objects.filter(role=role).delete()
        
        # Add new permissions
        for perm_id in permission_ids:
            try:
                permission = Permission.objects.get(id=perm_id)
                RolePermission.objects.create(role=role, permission=permission)
            except Permission.DoesNotExist:
                continue
        
        messages.success(request, f'Permissions updated for role "{role.name}"')
        return redirect('access_control:roles_and_permissions_list')
    
    # Get currently assigned permissions
    assigned_permissions = RolePermission.objects.filter(
        role=role
    ).values_list('permission_id', flat=True)
    
    context = {
        'role': role,
        'all_permissions': all_permissions,
        'assigned_permissions': list(assigned_permissions),
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/manage_role_permissions.html', context)


@login_required(login_url='auth:login')
def create_role(request):
    """
    Create a new role.
    """
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role created successfully!')
            return redirect('access_control:roles_and_permissions_list')
    else:
        form = RoleForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/role_form.html', context)


@login_required(login_url='auth:login')
def edit_role(request, role_id):
    """
    Edit an existing role.
    """
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{role.name}" updated successfully!')
            return redirect('access_control:role_detail', role_id=role.id)
    else:
        form = RoleForm(instance=role)
    
    context = {
        'form': form,
        'role': role,
        'action': 'Edit',
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/role_form.html', context)


@login_required(login_url='auth:login')
def delete_role(request, role_id):
    """
    Delete a role. Only superuser or staff can delete roles.
    """
    # Check if user is superuser or staff
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to delete roles.')
        return redirect('access_control:roles_and_permissions_list')
    
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        role_name = role.name
        role.delete()
        messages.success(request, f'Role "{role_name}" deleted successfully!')
        return redirect('access_control:roles_and_permissions_list')
    
    context = {
        'role': role,
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/confirm_delete_role.html', context)


@login_required(login_url='auth:login')
def create_permission(request):
    """
    Create a new permission.
    """
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Permission created successfully!')
            return redirect('access_control:roles_and_permissions_list')
    else:
        form = PermissionForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/permission_form.html', context)


@login_required(login_url='auth:login')
def edit_permission(request, permission_id):
    """
    Edit an existing permission.
    """
    permission = get_object_or_404(Permission, id=permission_id)
    
    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            messages.success(request, f'Permission "{permission.name}" updated successfully!')
            return redirect('access_control:permission_detail', permission_id=permission.id)
    else:
        form = PermissionForm(instance=permission)
    
    context = {
        'form': form,
        'permission': permission,
        'action': 'Edit',
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/permission_form.html', context)


@login_required(login_url='auth:login')
def delete_permission(request, permission_id):
    """
    Delete a permission. Only superuser or staff can delete permissions.
    """
    # Check if user is superuser or staff
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to delete permissions.')
        return redirect('access_control:roles_and_permissions_list')
    
    permission = get_object_or_404(Permission, id=permission_id)
    
    if request.method == 'POST':
        perm_name = permission.name
        permission.delete()
        messages.success(request, f'Permission "{perm_name}" deleted successfully!')
        return redirect('access_control:roles_and_permissions_list')
    
    context = {
        'permission': permission,
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/confirm_delete_permission.html', context)


@login_required(login_url='auth:login')
def user_role_permissions(request):
    """
    View and manage users with their assigned roles and permissions.
    Displays all users with pagination, search, and filtering capabilities.
    """
    # Get all users
    users_queryset = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users_queryset = users_queryset.filter(
            first_name__icontains=search_query
        ) | users_queryset.filter(
            last_name__icontains=search_query
        ) | users_queryset.filter(
            email__icontains=search_query
        )
    
    # Pagination
    page_num = request.GET.get('page', 1)
    rows_per_page = request.GET.get('rows_per_page', 10)
    
    paginator = Paginator(users_queryset, rows_per_page)
    try:
        page = paginator.page(page_num)
    except (EmptyPage, PageNotAnInteger):
        page = paginator.page(1)
    
    # Get statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    roles_count = Role.objects.count()
    permissions_count = Permission.objects.count()
    
    context = {
        'users': page.object_list,
        'page_obj': page,
        'paginator': paginator,
        'total_users': total_users,
        'active_users': active_users,
        'roles_count': roles_count,
        'permissions_count': permissions_count,
        'expiring_count': 18,  # Placeholder for subscription expiring count
        'search_query': search_query,
        'rows_per_page': rows_per_page,
        'current_section': 'roles_permissions',
    }
    
    return render(request, 'access_control/roles_permissions.html', context)
