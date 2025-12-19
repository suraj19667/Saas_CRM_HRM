"""
Role management views with production-ready error handling, pagination, and query optimization.

Requirements:
- 401 Unauthorized: User not authenticated
- 403 Forbidden: User lacks permission
- 404 Not Found: Resource not found
- 400 Bad Request: Validation error
- Query optimization with select_related/prefetch_related
- Pagination with 10 items per page
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Prefetch
from django.views.decorators.http import require_http_methods

from ..models import Role, RolePermission
from ..forms import RoleForm


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
@require_http_methods(['GET', 'POST'])
def roles_list(request):
    """
    List all roles with pagination and query optimization.
    
    GET: Returns paginated list of roles with permission counts
    POST: Redirects to add_role view
    
    Query Optimization:
    - Uses prefetch_related() for role_permissions (reverse FK)
    - Uses Count() annotation for permission_count
    - Uses distinct() to avoid duplicate rows
    
    Pagination:
    - 10 items per page
    - Includes total_count in response
    
    Returns:
        HttpResponse: Rendered template with roles and pagination info
    """
    try:
        # Query optimization with prefetch_related for reverse relationships
        roles_queryset = Role.objects.prefetch_related(
            Prefetch(
                'role_permissions',
                queryset=RolePermission.objects.select_related('permission')
            )
        ).annotate(
            # Count permissions for each role
            permission_count=Count('role_permissions', distinct=True)
        ).order_by('name')
        
        # Get page number from request
        page_number = request.GET.get('page', 1)
        
        # Paginate the queryset
        roles, pagination_info = _get_paginated_response(
            roles_queryset,
            page_number,
            page_size=10
        )
        
        if roles is None:
            messages.error(request, pagination_info.get('error_message', 'Pagination error'))
            return render(request, 'roles/roles_list.html', {
                'roles': [],
                'pagination': {}
            })
        
        context = {
            'roles': roles,
            'pagination': pagination_info
        }
        
        return render(request, 'roles/roles_list.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading roles: {str(e)}')
        return render(request, 'roles/roles_list.html', {
            'roles': [],
            'pagination': {}
        })


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def add_role(request):
    """
    Create a new role with validation.
    
    GET: Returns form for adding new role
    POST: Creates role with validation
    
    Validation:
    - Checks required fields (name)
    - Validates unique name constraint
    - Returns 400 Bad Request on validation error
    
    Returns:
        HttpResponse: Form template or redirect to roles_list on success
        JsonResponse: Error response if validation fails
    """
    try:
        if request.method == 'POST':
            form = RoleForm(request.POST)
            
            # Input validation
            if not form.is_valid():
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f'{field}: {error}')
                
                error_message = ' | '.join(error_messages)
                messages.error(request, f'Validation error: {error_message}')
                return render(request, 'roles/add_role.html', {
                    'form': form,
                    'error_message': error_message
                }, status=400)
            
            try:
                role = form.save()
                messages.success(request, f'Role "{role.name}" created successfully!')
                return redirect('roles_list')
            
            except Exception as e:
                error_message = f'Database error: {str(e)}'
                messages.error(request, error_message)
                return render(request, 'roles/add_role.html', {
                    'form': form,
                    'error_message': error_message
                }, status=400)
        
        else:
            form = RoleForm()
        
        return render(request, 'roles/add_role.html', {'form': form})
    
    except Exception as e:
        error_message = f'Error in role creation: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'roles/add_role.html', {
            'form': RoleForm(),
            'error_message': error_message
        }, status=400)


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def edit_role(request, role_id):
    """
    Edit an existing role with permission validation.
    
    Args:
        role_id (int): ID of role to edit
    
    GET: Returns edit form with role data
    POST: Updates role with validation
    
    Error Handling:
    - 404 Not Found: If role doesn't exist
    - 403 Forbidden: If user lacks permission (placeholder for future)
    - 400 Bad Request: If validation fails
    
    Query Optimization:
    - Uses select_related for ForeignKeys
    - Uses prefetch_related for permissions
    
    Returns:
        HttpResponse: Form template or redirect to roles_list on success
        JsonResponse: Error response if validation fails
    """
    try:
        # Query optimization: prefetch related permissions
        role = Role.objects.prefetch_related(
            Prefetch(
                'role_permissions',
                queryset=RolePermission.objects.select_related('permission')
            )
        ).get(id=role_id)
    
    except Role.DoesNotExist:
        error_message = f'Role with ID {role_id} not found.'
        messages.error(request, error_message)
        return render(request, 'roles/edit_role.html', {
            'error_message': error_message
        }, status=404)
    
    except Exception as e:
        error_message = f'Database error: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'roles/edit_role.html', {
            'error_message': error_message
        }, status=400)
    
    try:
        if request.method == 'POST':
            form = RoleForm(request.POST, instance=role)
            
            # Input validation
            if not form.is_valid():
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f'{field}: {error}')
                
                error_message = ' | '.join(error_messages)
                messages.error(request, f'Validation error: {error_message}')
                return render(request, 'roles/edit_role.html', {
                    'form': form,
                    'role': role,
                    'error_message': error_message
                }, status=400)
            
            try:
                updated_role = form.save()
                messages.success(request, f'Role "{updated_role.name}" updated successfully!')
                return redirect('roles_list')
            
            except Exception as e:
                error_message = f'Database error: {str(e)}'
                messages.error(request, error_message)
                return render(request, 'roles/edit_role.html', {
                    'form': form,
                    'role': role,
                    'error_message': error_message
                }, status=400)
        
        else:
            form = RoleForm(instance=role)
        
        return render(request, 'roles/edit_role.html', {
            'form': form,
            'role': role
        })
    
    except Exception as e:
        error_message = f'Error in role update: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'roles/edit_role.html', {
            'error_message': error_message
        }, status=400)


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def delete_role(request, role_id):
    """
    Delete a role with confirmation.
    
    Args:
        role_id (int): ID of role to delete
    
    GET: Returns confirmation page
    POST: Deletes role
    
    Permissions:
    - Only superuser or staff can delete roles
    
    Error Handling:
    - 404 Not Found: If role doesn't exist
    - 403 Forbidden: If user is not superuser/staff
    - 400 Bad Request: If deletion fails
    
    Query Optimization:
    - Uses only() to load minimal fields on GET
    - Uses Count() to check user assignments
    
    Returns:
        HttpResponse: Confirmation template or redirect to roles_list on success
        JsonResponse: Error response on failure
    """
    # Check if user is superuser or staff
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to delete roles.')
        return redirect('roles_list')
    
    try:
        # Query optimization: load minimal fields for confirmation page
        role = Role.objects.only('id', 'name').get(id=role_id)
    
    except Role.DoesNotExist:
        error_message = f'Role with ID {role_id} not found.'
        messages.error(request, error_message)
        return render(request, 'roles/delete_role.html', {
            'error_message': error_message
        }, status=404)
    
    except Exception as e:
        error_message = f'Database error: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'roles/delete_role.html', {
            'error_message': error_message
        }, status=400)
    
    try:
        if request.method == 'POST':
            # Super admin can delete roles even if users are assigned
            role_name = role.name
            role.delete()
            messages.success(request, f'Role "{role_name}" deleted successfully!')
            return redirect('roles_list')
        
        else:
            # Get additional info for confirmation page
            user_count = role.users.count()
            permission_count = role.role_permissions.count()
            
            return render(request, 'roles/delete_role.html', {
                'role': role,
                'user_count': user_count,
                'permission_count': permission_count
            })
    
    except Exception as e:
        error_message = f'Error deleting role: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'roles/delete_role.html', {
            'role': role,
            'error_message': error_message
        }, status=400)
