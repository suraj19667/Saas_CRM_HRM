"""
REST API views with comprehensive error handling, pagination, and query optimization.

These views provide JSON API endpoints following REST principles with:
- Proper HTTP status codes (400, 401, 403, 404, 500)
- Input validation and error_message responses
- Query optimization with select_related/prefetch_related
- Pagination with 10 items per page
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from django.urls import reverse
import json

from .models import Role, Permission, RolePermission, CustomUser, PaymentTransaction, Tenant
from .api_utils import (
    APIResponse,
    ValidationError,
    PaginationHelper,
    ErrorHandler
)


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_roles_list(request):
    """
    API endpoint to list all roles with pagination.
    
    GET Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    - search: Search query for role name/description
    
    Response:
    {
        'success': true,
        'data': {
            'items': [...],
            'pagination': {
                'current_page': 1,
                'total_pages': 5,
                'total_count': 47,
                'page_size': 10
            }
        }
    }
    
    Error Responses:
    - 400 Bad Request: Invalid pagination parameters
    - 401 Unauthorized: User not authenticated
    
    Query Optimization:
    - Uses prefetch_related() for role_permissions
    - Uses Count() annotation for permission_count
    """
    try:
        # Get pagination parameters with validation
        try:
            page_number = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            # Validate page size (max 100)
            if page_size > 100:
                page_size = 100
            if page_size < 1:
                page_size = 10
        except (ValueError, TypeError):
            return APIResponse.error(
                'Invalid pagination parameters. page and page_size must be integers.',
                status_code=400
            )
        
        # Build optimized queryset
        roles_queryset = Role.objects.prefetch_related(
            Prefetch(
                'role_permissions',
                queryset=RolePermission.objects.select_related('permission')
            )
        ).annotate(
            permission_count=Count('role_permissions', distinct=True),
            user_count=Count('users', distinct=True)
        )
        
        # Apply search filter
        search_query = request.GET.get('search', '').strip()
        if search_query:
            roles_queryset = roles_queryset.filter(
                name__icontains=search_query
            ) | roles_queryset.filter(
                description__icontains=search_query
            )
        
        # Order by name
        roles_queryset = roles_queryset.order_by('name')
        
        # Paginate
        items, pagination_info, error = PaginationHelper.paginate(
            roles_queryset,
            page_number,
            page_size
        )
        
        if error:
            return APIResponse.error(error, status_code=400)
        
        # Serialize roles
        serialized_items = [
            {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'permission_count': role.permission_count,
                'user_count': role.user_count,
                'created_at': role.created_at.isoformat(),
                'updated_at': role.updated_at.isoformat()
            }
            for role in items
        ]
        
        # Return shape expected by frontend templates
        return JsonResponse({
            'success': True,
            'roles': serialized_items,
            'pagination': pagination_info,
            'status': 200
        }, status=200)
    
    except Exception as e:
        return APIResponse.error(
            f'Server error: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_role_detail(request, role_id):
    """
    API endpoint to get detailed information about a specific role.
    
    Path Parameters:
    - role_id: ID of the role
    
    Response:
    {
        'success': true,
        'data': {
            'id': 1,
            'name': 'Admin',
            'description': '...',
            'permissions': [...],
            'user_count': 5,
            'created_at': '2024-01-01T00:00:00Z'
        }
    }
    
    Error Responses:
    - 404 Not Found: Role not found
    - 400 Bad Request: Invalid role_id
    
    Query Optimization:
    - Uses select_related for role
    - Uses prefetch_related for permissions
    """
    try:
        # Validate role_id
        try:
            role_id = int(role_id)
        except (ValueError, TypeError):
            return APIResponse.error('Invalid role ID.', status_code=400)
        
        # Query with optimization
        try:
            role = Role.objects.prefetch_related(
                Prefetch(
                    'role_permissions',
                    queryset=RolePermission.objects.select_related('permission')
                )
            ).annotate(
                user_count=Count('users', distinct=True)
            ).get(id=role_id)
        
        except Role.DoesNotExist:
            return ErrorHandler.handle_not_found('Role', role_id)
        
        # Serialize permissions
        permissions = [
            {
                'id': rp.permission.id,
                'name': rp.permission.name,
                'codename': rp.permission.codename,
                'module': rp.permission.module,
                'granted_at': rp.granted_at.isoformat()
            }
            for rp in role.role_permissions.all()
        ]
        
        return JsonResponse({
            'success': True,
            'role': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'permissions': permissions,
                'user_count': role.user_count,
                'created_at': role.created_at.isoformat(),
                'updated_at': role.updated_at.isoformat()
            },
            'status': 200
        }, status=200)
    
    except Exception as e:
        return APIResponse.error(
            f'Server error: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_permissions_list(request):
    """
    API endpoint to list all permissions with pagination and filtering.
    
    GET Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    - module: Filter by module (optional)
    - search: Search query for permission name/codename
    
    Response:
    {
        'success': true,
        'data': {
            'items': [...],
            'pagination': {...},
            'modules': ['users', 'roles', 'permissions']
        }
    }
    
    Error Responses:
    - 400 Bad Request: Invalid parameters
    - 401 Unauthorized: User not authenticated
    
    Query Optimization:
    - Uses prefetch_related() for permission_roles
    - Uses Count() annotation for role_count
    """
    try:
        # Validate pagination parameters
        try:
            page_number = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            if page_size > 100:
                page_size = 100
            if page_size < 1:
                page_size = 10
        except (ValueError, TypeError):
            return APIResponse.error(
                'Invalid pagination parameters.',
                status_code=400
            )
        
        # Build optimized queryset
        permissions_queryset = Permission.objects.prefetch_related(
            Prefetch(
                'permission_roles',
                queryset=RolePermission.objects.select_related('role')
            )
        ).annotate(
            role_count=Count('permission_roles', distinct=True)
        )
        
        # Apply module filter
        module = request.GET.get('module', '').strip()
        if module:
            permissions_queryset = permissions_queryset.filter(module=module)
        
        # Apply search filter
        search_query = request.GET.get('search', '').strip()
        if search_query:
            permissions_queryset = permissions_queryset.filter(
                name__icontains=search_query
            ) | permissions_queryset.filter(
                codename__icontains=search_query
            )
        
        # Order by module and name
        permissions_queryset = permissions_queryset.order_by('module', 'name')
        
        # Get unique modules
        modules = list(
            Permission.objects.values_list('module', flat=True).distinct()
        )
        
        # Paginate
        items, pagination_info, error = PaginationHelper.paginate(
            permissions_queryset,
            page_number,
            page_size
        )
        
        if error:
            return APIResponse.error(error, status_code=400)
        
        # Serialize permissions
        serialized_items = [
            {
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'module': perm.module,
                'description': perm.description,
                'role_count': perm.role_count,
                'created_at': perm.created_at.isoformat()
            }
            for perm in items
        ]
        
        # Build modules map for frontend convenience
        modules_map = {}
        for perm in serialized_items:
            modules_map.setdefault(perm['module'], []).append(perm)

        return JsonResponse({
            'success': True,
            'permissions': serialized_items,
            'modules': modules_map,
            'pagination': pagination_info,
            'status': 200
        }, status=200)
    
    except Exception as e:
        return APIResponse.error(
            f'Server error: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_users_list(request):
    """
    API endpoint to list all users with pagination, filtering, and search.
    
    GET Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    - role: Filter by role ID (optional)
    - status: Filter by status - active, inactive, verified, unverified (optional)
    - search: Search in username, email, first_name, last_name (optional)
    
    Response:
    {
        'success': true,
        'data': {
            'items': [...],
            'pagination': {...},
            'total_stats': {
                'total_users': 100,
                'active_users': 85,
                'verified_users': 90
            }
        }
    }
    
    Error Responses:
    - 400 Bad Request: Invalid parameters
    - 401 Unauthorized: User not authenticated
    
    Query Optimization:
    - Uses select_related() for role ForeignKey
    - Uses Count() annotation for statistics
    """
    try:
        # Validate pagination
        try:
            page_number = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            if page_size > 100:
                page_size = 100
            if page_size < 1:
                page_size = 10
        except (ValueError, TypeError):
            return APIResponse.error(
                'Invalid pagination parameters.',
                status_code=400
            )
        
        # Build optimized queryset
        users_queryset = CustomUser.objects.select_related('role')
        
        # Apply role filter
        role_id = request.GET.get('role', '').strip()
        if role_id:
            try:
                role_id = int(role_id)
                users_queryset = users_queryset.filter(role_id=role_id)
            except (ValueError, TypeError):
                return APIResponse.error('Invalid role ID.', status_code=400)
        
        # Apply status filter
        status = request.GET.get('status', '').strip().lower()
        if status == 'active':
            users_queryset = users_queryset.filter(is_active=True)
        elif status == 'inactive':
            users_queryset = users_queryset.filter(is_active=False)
        elif status == 'verified':
            users_queryset = users_queryset.filter(is_verified=True)
        elif status == 'unverified':
            users_queryset = users_queryset.filter(is_verified=False)
        
        # Apply search filter
        search_query = request.GET.get('search', '').strip()
        if search_query:
            from django.db.models import Q
            users_queryset = users_queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Order by date joined
        users_queryset = users_queryset.order_by('-date_joined')
        
        # Get statistics
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        verified_users = CustomUser.objects.filter(is_verified=True).count()
        
        # Paginate
        items, pagination_info, error = PaginationHelper.paginate(
            users_queryset,
            page_number,
            page_size
        )
        
        if error:
            return APIResponse.error(error, status_code=400)
        
        # Serialize users
        serialized_items = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f'{user.first_name} {user.last_name}'.strip(),
                'role': {
                    'id': user.role.id,
                    'name': user.role.name
                } if user.role else None,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'date_joined': user.date_joined.isoformat(),
                'phone': user.phone if hasattr(user, 'phone') else None
            }
            for user in items
        ]
        
        # Return shape expected by frontend templates
        return JsonResponse({
            'success': True,
            'users': serialized_items,
            'pagination': pagination_info,
            'total_stats': {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users
            },
            'status': 200
        }, status=200)
    
    except Exception as e:
        return APIResponse.error(
            f'Server error: {str(e)}',
            status_code=500
        )


@csrf_exempt
@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def api_user_create(request):
    """Create a new user (assign role optionally). Requires `create_user` permission."""
    try:
        if not (request.user.is_superuser or request.user.is_staff or request.user.has_permission('create_user')):
            return ErrorHandler.handle_forbidden()

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return ErrorHandler.handle_bad_request('Invalid JSON payload')

        valid, err = ValidationError.validate_required_fields(payload, ['username', 'email', 'password'])
        if not valid:
            return ErrorHandler.handle_bad_request(err)

        username = payload.get('username')
        email = payload.get('email')
        password = payload.get('password')
        first_name = payload.get('first_name', '')
        last_name = payload.get('last_name', '')
        role_id = payload.get('role_id')
        is_staff = bool(payload.get('is_staff', False))
        is_active = bool(payload.get('is_active', True))

        user = CustomUser.objects.create_user(username=username, email=email, password=password)
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = is_staff
        user.is_active = is_active
        if role_id:
            try:
                role = Role.objects.get(id=int(role_id))
                user.role = role
            except Exception:
                pass
        user.save()

        return JsonResponse({'success': True, 'message': 'User created', 'user_id': user.id}, status=201)
    except Exception as e:
        return ErrorHandler.handle_server_error(str(e))


@csrf_exempt
@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def api_user_update(request, user_id):
    """Update user. Requires `edit_user` permission."""
    try:
        try:
            target_user = CustomUser.objects.get(id=int(user_id))
        except CustomUser.DoesNotExist:
            return ErrorHandler.handle_not_found('User', user_id)

        # Only allow if has permission
        if not (request.user.is_superuser or request.user.is_staff or request.user.has_permission('edit_user')):
            return ErrorHandler.handle_forbidden()

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return ErrorHandler.handle_bad_request('Invalid JSON payload')

        # Update allowed fields
        allowed = ['first_name', 'last_name', 'email', 'phone', 'is_active', 'is_staff', 'role_id']
        for key in allowed:
            if key in payload:
                if key == 'role_id':
                    try:
                        role = Role.objects.get(id=int(payload['role_id']))
                        target_user.role = role
                    except Exception:
                        target_user.role = None
                else:
                    setattr(target_user, key, payload[key])

        # handle password change only if provided and requester has create_user or is superuser
        if 'password' in payload and (request.user.is_superuser or request.user.has_permission('create_user')):
            target_user.set_password(payload['password'])

        target_user.save()
        return JsonResponse({'success': True, 'message': 'User updated'}, status=200)

    except Exception as e:
        return ErrorHandler.handle_server_error(str(e))


@csrf_exempt
@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def api_user_delete(request, user_id):
    """Delete user. Requires `delete_user` permission."""
    try:
        try:
            target_user = CustomUser.objects.get(id=int(user_id))
        except CustomUser.DoesNotExist:
            return ErrorHandler.handle_not_found('User', user_id)

        if not (request.user.is_superuser or request.user.is_staff or request.user.has_permission('delete_user')):
            return ErrorHandler.handle_forbidden()

        target_user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted'}, status=200)
    except Exception as e:
        return ErrorHandler.handle_server_error(str(e))


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_me(request):
    """Return logged in user information, role and permissions."""
    try:
        user = request.user
        role = None
        permissions = []
        if user.role:
            role = {
                'id': user.role.id,
                'name': user.role.name,
                'description': user.role.description
            }
            permissions = user.get_permission_codenames()
        elif user.is_superuser or user.is_staff:
            # return all permission codenames
            permissions = list(Permission.objects.values_list('codename', flat=True))

        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role,
                'permissions': permissions
            },
            'status': 200
        }, status=200)
    except Exception as e:
        return ErrorHandler.handle_server_error(str(e))


# ========================
# Subscription Plan API Views
# ========================

def is_super_admin(user):
    """Check if user is a super admin (superuser or staff)."""
    return user.is_superuser or user.is_staff


def payment_success_handler(request, razorpay_payment_id):
    transaction = get_object_or_404(PaymentTransaction, razorpay_payment_id=razorpay_payment_id)
    tenant = transaction.tenant

    # Update transaction status
    transaction.status = "PAID"
    transaction.save()

    # Update tenant details
    tenant.status = "active"
    tenant.subscription_start_date = now()
    tenant.subscription_end_date = now() + transaction.plan.duration
    tenant.save()

    # Redirect to tenant dashboard
    return redirect(reverse("tenant_dashboard", kwargs={"tenant_slug": tenant.slug}))
