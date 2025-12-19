"""
Permission management views with production-ready error handling, pagination, and query optimization.

Requirements:
- 401 Unauthorized: User not authenticated
- 403 Forbidden: User lacks permission
- 404 Not Found: Resource not found
- 400 Bad Request: Validation error
- Query optimization with select_related/prefetch_related
- Pagination with 10 items per page
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Prefetch, Q
from django.views.decorators.http import require_http_methods

from ..models import Permission, RolePermission, Role
from ..forms import PermissionForm


def _get_error_response(error_message, status_code=400):
    """
    Helper function to return consistent error responses.
    
    Args:
        error_message (str): The error message to return
        status_code (int): HTTP status code (default: 400)
    
    Returns:
        JsonResponse: JSON error response with error_message field
    """
    return JsonResponse(
        {'error_message': error_message, 'status': status_code},
        status=status_code
    )


def _get_paginated_response(queryset, page_number, page_size=10):
    """
    Helper function to paginate queryset and return paginated response.
    
    Args:
        queryset: Django ORM queryset
        page_number (int): Page number requested
        page_size (int): Items per page (default: 10)
    
    Returns:
        tuple: (paginated_items, pagination_info) or (None, error_response)
    """
    try:
        paginator = Paginator(queryset, page_size)
        
        try:
            page = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
        
        pagination_info = {
            'current_page': page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
        }
        
        return page.object_list, pagination_info
    except Exception as e:
        return None, _get_error_response(f'Pagination error: {str(e)}', 400)


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def permissions_list(request):
    """
    List all permissions with filtering, pagination, and query optimization.
    
    GET Parameters:
    - page: Page number (default: 1)
    - module: Filter by module (optional)
    - search: Search in name, codename, description (optional)
    - status: Filter by status - active, inactive (optional)
    
    Query Optimization:
    - Uses prefetch_related for role_permissions (reverse FK)
    - Uses Count() for role count
    - Uses distinct() to avoid duplicates
    
    Pagination:
    - 10 items per page
    - Includes total_count in response
    
    Returns:
        HttpResponse: Rendered permissions list template with pagination
    """
    try:
        # Base queryset with optimizations
        permissions_queryset = Permission.objects.prefetch_related(
            Prefetch(
                'permission_roles',
                queryset=RolePermission.objects.select_related('role')
            )
        ).annotate(
            role_count=Count('permission_roles', distinct=True)
        ).order_by('module', 'name')
        
        # Apply module filter
        module_filter = request.GET.get('module', '').strip()
        if module_filter:
            permissions_queryset = permissions_queryset.filter(module=module_filter)
        
        # Apply status filter
        status_filter = request.GET.get('status', '').strip().lower()
        if status_filter == 'active':
            permissions_queryset = permissions_queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            permissions_queryset = permissions_queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = request.GET.get('search', '').strip()
        if search_query:
            permissions_queryset = permissions_queryset.filter(
                Q(name__icontains=search_query) |
                Q(codename__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Get available modules for filter dropdown
        modules = Permission.MODULE_CHOICES
        
        # Get page number
        page_number = request.GET.get('page', 1)
        
        # Paginate the queryset
        permissions, pagination_info = _get_paginated_response(
            permissions_queryset,
            page_number,
            page_size=10
        )
        
        if permissions is None:
            messages.error(request, pagination_info.get('error_message', 'Pagination error'))
            return render(request, 'permissions/permissions_list.html', {
                'permissions': [],
                'modules': modules,
                'pagination': {}
            })
        
        context = {
            'permissions': permissions,
            'modules': modules,
            'pagination': pagination_info,
            'selected_module': module_filter,
            'selected_status': status_filter,
            'search_query': search_query,
        }
        
        return render(request, 'permissions/permissions_list.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading permissions: {str(e)}')
        return render(request, 'permissions/permissions_list.html', {
            'permissions': [],
            'modules': Permission.MODULE_CHOICES,
            'pagination': {}
        })


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def add_permission(request):
    """
    Create a new permission with validation.
    
    GET: Returns form for adding new permission
    POST: Creates permission with validation
    
    Validation:
    - name: Must be unique
    - codename: Must be unique
    - module: Must be valid choice
    
    Returns:
        GET: HttpResponse rendered form
        POST: Redirect to permissions list on success, re-render form on error
    """
    try:
        if request.method == 'POST':
            form = PermissionForm(request.POST)
            if form.is_valid():
                permission = form.save()
                messages.success(request, f'Permission "{permission.name}" created successfully!')
                return redirect('permissions:permissions_list')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = PermissionForm()
        
        context = {
            'form': form,
            'title': 'Add Permission'
        }
        return render(request, 'permissions/add_permission.html', context)
    
    except Exception as e:
        messages.error(request, f'Error creating permission: {str(e)}')
        return redirect('permissions:permissions_list')


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def edit_permission(request, permission_id):
    """
    Edit an existing permission with validation.
    
    GET: Returns form for editing permission
    POST: Updates permission with validation
    
    Parameters:
    - permission_id: ID of permission to edit
    
    Returns:
        GET: HttpResponse rendered form
        POST: Redirect to permissions list on success, re-render form on error
        404: If permission not found
    """
    try:
        permission = get_object_or_404(Permission, id=permission_id)
        
        if request.method == 'POST':
            form = PermissionForm(request.POST, instance=permission)
            if form.is_valid():
                permission = form.save()
                messages.success(request, f'Permission "{permission.name}" updated successfully!')
                return redirect('permissions:permissions_list')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = PermissionForm(instance=permission)
        
        context = {
            'form': form,
            'permission': permission,
            'title': 'Edit Permission'
        }
        return render(request, 'permissions/edit_permission.html', context)
    
    except Permission.DoesNotExist:
        messages.error(request, 'Permission not found!')
        return redirect('permissions:permissions_list')
    except Exception as e:
        messages.error(request, f'Error updating permission: {str(e)}')
        return redirect('permissions:permissions_list')


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def delete_permission(request, permission_id):
    """
    Delete a permission with confirmation.
    
    Permissions:
    - Only superuser or staff can delete permissions
    
    Parameters:
    - permission_id: ID of permission to delete
    
    Returns:
        Redirect to permissions list on success
        JSON error on validation failure
    """
    # Check if user is superuser or staff
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to delete permissions.')
        return redirect('permissions:permissions_list')
    
    try:
        permission = get_object_or_404(Permission, id=permission_id)
        
        # Super admin can delete permissions even if assigned to roles
    except Permission.DoesNotExist:
        messages.error(request, 'Permission not found!')
        return redirect('permissions:permissions_list')
    except Exception as e:
        messages.error(request, f'Error deleting permission: {str(e)}')
        return redirect('permissions:permissions_list')

        
        pagination_info = {
            'current_page': page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
        }
        
        return page.object_list, pagination_info
    except Exception as e:
        return None, _get_error_response(f'Pagination error: {str(e)}', 400)


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def permissions_list(request):
    """
    List all permissions with pagination, filtering, and query optimization.
    
    GET Parameters:
    - page: Page number (default: 1)
    - module: Filter by module (optional)
    - search: Search in name or description (optional)
    
    Query Optimization:
    - Uses prefetch_related() for permission_roles (reverse FK)
    - Uses Count() annotation for role_count
    - Uses distinct() to avoid duplicate rows
    - Uses only() for minimal field loading when applicable
    
    Pagination:
    - 10 items per page
    - Includes total_count in response
    
    Returns:
        HttpResponse: Rendered template with permissions and pagination info
    """
    try:
        # Build base queryset with optimizations
        permissions_queryset = Permission.objects.prefetch_related(
            Prefetch(
                'permission_roles',
                queryset=RolePermission.objects.select_related('role')
            )
        ).annotate(
            # Count roles that have this permission
            role_count=Count('permission_roles', distinct=True)
        )
        
        # Apply filters
        module_filter = request.GET.get('module', '').strip()
        if module_filter:
            permissions_queryset = permissions_queryset.filter(module=module_filter)
        
        search_query = request.GET.get('search', '').strip()
        if search_query:
            permissions_queryset = permissions_queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(codename__icontains=search_query)
            )
        
        # Order by module and name
        permissions_queryset = permissions_queryset.order_by('module', 'name')
        
        # Get unique modules for filter dropdown
        modules = Permission.objects.values_list('module', flat=True).distinct()
        
        # Get page number from request
        page_number = request.GET.get('page', 1)
        
        # Paginate the queryset
        permissions, pagination_info = _get_paginated_response(
            permissions_queryset,
            page_number,
            page_size=10
        )
        
        if permissions is None:
            messages.error(request, 'Pagination error occurred.')
            return render(request, 'permissions/permissions_list.html', {
                'permissions': [],
                'pagination': {},
                'modules': modules
            })
        
        context = {
            'permissions': permissions,
            'pagination': pagination_info,
            'modules': modules,
            'current_module': module_filter,
            'search_query': search_query
        }
        
        return render(request, 'permissions/permissions_list.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading permissions: {str(e)}')
        return render(request, 'permissions/permissions_list.html', {
            'permissions': [],
            'pagination': {}
        })


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def permission_detail(request, permission_id):
    """
    View detailed information about a specific permission.
    
    Args:
        permission_id (int): ID of permission to view
    
    Query Optimization:
    - Uses prefetch_related for related roles
    - Uses select_related for role data
    
    Error Handling:
    - 404 Not Found: If permission doesn't exist
    
    Returns:
        HttpResponse: Rendered permission detail template
    """
    try:
        # Query optimization: prefetch related roles
        permission = Permission.objects.prefetch_related(
            Prefetch(
                'permission_roles',
                queryset=RolePermission.objects.select_related('role')
            )
        ).get(id=permission_id)
    
    except Permission.DoesNotExist:
        error_message = f'Permission with ID {permission_id} not found.'
        messages.error(request, error_message)
        return redirect('permissions_list')
    
    except Exception as e:
        error_message = f'Database error: {str(e)}'
        messages.error(request, error_message)
        return redirect('permissions_list')
    
    context = {
        'permission': permission,
        'related_roles': permission.permission_roles.all(),
        'role_count': permission.permission_roles.count()
    }
    
    return render(request, 'permissions/permission_detail.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def bulk_assign_permissions(request):
    """
    Bulk assign permissions to roles.
    
    POST Parameters:
    - role_id: ID of role to assign permissions to
    - permission_ids: List of permission IDs to assign
    
    Validation:
    - Checks role exists
    - Validates permission IDs
    - Prevents duplicate assignments
    
    Error Handling:
    - 400 Bad Request: Invalid input
    - 404 Not Found: Role or permissions not found
    
    Returns:
        HttpResponse: Form template (GET) or redirect on success (POST)
        JsonResponse: Error response on validation failure
    """
    try:
        if request.method == 'POST':
            try:
                role_id = int(request.POST.get('role_id', 0))
            except (ValueError, TypeError):
                messages.error(request, 'Invalid role ID provided.')
                return render(request, 'permissions/bulk_assign.html', {
                    'error_message': 'Invalid role ID'
                }, status=400)
            
            # Validate role exists
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                error_message = f'Role with ID {role_id} not found.'
                messages.error(request, error_message)
                return render(request, 'permissions/bulk_assign.html', {
                    'error_message': error_message
                }, status=404)
            
            # Get permission IDs from POST data
            permission_ids = request.POST.getlist('permission_ids')
            
            if not permission_ids:
                messages.warning(request, 'No permissions selected.')
                return render(request, 'permissions/bulk_assign.html', {
                    'roles': Role.objects.all(),
                    'permissions': Permission.objects.all(),
                    'warning_message': 'No permissions selected'
                })
            
            # Validate permission IDs exist
            try:
                permission_ids = [int(pid) for pid in permission_ids]
                permissions = Permission.objects.filter(id__in=permission_ids)
                
                if len(permissions) != len(permission_ids):
                    messages.error(request, 'One or more permission IDs are invalid.')
                    return render(request, 'permissions/bulk_assign.html', {
                        'error_message': 'Invalid permission IDs'
                    }, status=400)
            
            except (ValueError, TypeError):
                messages.error(request, 'Permission IDs must be integers.')
                return render(request, 'permissions/bulk_assign.html', {
                    'error_message': 'Invalid permission ID format'
                }, status=400)
            
            try:
                # Get existing permissions for this role
                existing_perms = set(
                    role.role_permissions.values_list('permission_id', flat=True)
                )
                
                # Filter out already assigned permissions
                new_permission_ids = [pid for pid in permission_ids if pid not in existing_perms]
                
                # Bulk create new assignments
                role_permissions = [
                    RolePermission(role=role, permission_id=perm_id)
                    for perm_id in new_permission_ids
                ]
                
                created_count = len(RolePermission.objects.bulk_create(
                    role_permissions,
                    ignore_conflicts=True
                ))
                
                messages.success(
                    request,
                    f'{created_count} permission(s) assigned to role "{role.name}" successfully!'
                )
                return redirect('roles_list')
            
            except Exception as e:
                error_message = f'Database error: {str(e)}'
                messages.error(request, error_message)
                return render(request, 'permissions/bulk_assign.html', {
                    'error_message': error_message
                }, status=400)
        
        else:
            # GET request: show form
            roles = Role.objects.all().order_by('name')
            permissions = Permission.objects.all().order_by('module', 'name')
            
            context = {
                'roles': roles,
                'permissions': permissions,
                'modules': Permission.objects.values_list('module', flat=True).distinct()
            }
            
            return render(request, 'permissions/bulk_assign.html', context)
    
    except Exception as e:
        error_message = f'Error in bulk permission assignment: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'permissions/bulk_assign.html', {
            'error_message': error_message
        }, status=400)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def remove_permission_from_role(request, role_id, permission_id):
    """
    Remove a permission from a role.
    
    Args:
        role_id (int): ID of role
        permission_id (int): ID of permission to remove
    
    Error Handling:
    - 404 Not Found: Role or permission assignment not found
    - 400 Bad Request: Database error
    
    Returns:
        HttpResponse: Redirect to previous page or roles_list
    """
    try:
        try:
            role_perm = RolePermission.objects.select_related(
                'role', 'permission'
            ).get(role_id=role_id, permission_id=permission_id)
        
        except RolePermission.DoesNotExist:
            error_message = f'Permission assignment not found for role {role_id} and permission {permission_id}.'
            messages.error(request, error_message)
            return redirect('roles_list')
        
        role_name = role_perm.role.name
        permission_name = role_perm.permission.name
        
        role_perm.delete()
        messages.success(
            request,
            f'Permission "{permission_name}" removed from role "{role_name}" successfully!'
        )
        
        return redirect(request.META.get('HTTP_REFERER', 'roles_list'))
    
    except Exception as e:
        error_message = f'Error removing permission: {str(e)}'
        messages.error(request, error_message)
        return redirect('roles_list')
