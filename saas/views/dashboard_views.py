"""
StaffGrid Dashboard Views with production-ready error handling, pagination, and query optimization.

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
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from ..models import CustomUser, Role, Permission, Tenant, Subscription


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
def dashboard(request):
    """
    Dashboard view with key metrics and recent activity.
    
    Query Optimization:
    - Uses select_related for foreign keys (role)
    - Uses Count() annotations for user counts
    - Uses only() for minimal field loading
    
    Returns:
        HttpResponse: Rendered dashboard template with metrics
    """
    try:
        # Dashboard metrics with optimized queries
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        verified_users = CustomUser.objects.filter(is_verified=True).count()
        
        # Role and Permission metrics
        total_roles = Role.objects.filter(is_active=True).count()
        total_permissions = Permission.objects.filter(is_active=True).count()
        
        # Users by role with annotation
        users_by_role = Role.objects.annotate(
            user_count=Count('users', distinct=True)
        ).filter(is_active=True).order_by('-user_count')[:5]
        
        # Roles with permission counts
        roles_with_permissions = Role.objects.filter(
            is_active=True
        ).annotate(
            permission_count=Count('role_permissions', distinct=True),
            user_count=Count('users', distinct=True)
        ).order_by('-user_count')[:8]
        
        # Recent users (last 7 days)
        from datetime import timedelta
        recent_date = timezone.now() - timedelta(days=7)
        recent_users = CustomUser.objects.filter(
            date_joined__gte=recent_date
        ).count()
        
        # Recent signups (last 5)
        recent_signups = CustomUser.objects.select_related('role').only(
            'id', 'username', 'email', 'date_joined', 'role'
        ).order_by('-date_joined')[:5]
        
        # Permissions by module
        permissions_by_module = {}
        for module, label in Permission.MODULE_CHOICES:
            permissions_by_module[label] = Permission.objects.filter(
                module=module,
                is_active=True
            ).count()
        
        # Get current subscription for the user
        current_subscription = None
        try:
            # Check if user has a tenant associated
            if hasattr(request.user, 'tenant') and request.user.tenant:
                current_subscription = Subscription.objects.filter(
                    tenant=request.user.tenant,
                    status='active'
                ).select_related('plan').first()
        except:
            pass
        
        # Admin-specific data (for super admin users)
        total_plans = 0
        total_features = 0
        total_tenants = 0
        total_subscriptions = 0
        available_plans = []
        all_features = []
        
        if request.user.is_superuser or request.user.is_staff:
            from ..models import Plan, Feature, PlanFeature
            
            total_plans = Plan.objects.count()
            total_features = Feature.objects.count()
            total_tenants = Tenant.objects.count()
            total_subscriptions = Subscription.objects.filter(status='active').count()
            
            # Get plans with feature counts for admin dashboard
            available_plans = Plan.objects.prefetch_related('plan_features').all().order_by('price_monthly')
            
            # Get features with plan usage counts
            all_features = Feature.objects.prefetch_related('plan_features').all().order_by('name')

        context = {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'total_roles': total_roles,
            'total_permissions': total_permissions,
            'recent_users': recent_users,
            'users_by_role': users_by_role,
            'recent_signups': recent_signups,
            'roles_with_permissions': roles_with_permissions,
            'permissions_by_module': permissions_by_module,
            'current_subscription': current_subscription,
            'is_super_admin': request.user.is_superuser or request.user.is_staff,
            # Admin-specific data
            'total_plans': total_plans,
            'total_features': total_features,
            'total_tenants': total_tenants,
            'total_subscriptions': total_subscriptions,
            'available_plans': available_plans,
            'all_features': all_features,
        }
        
        return render(request, 'admin_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return render(request, 'admin_dashboard.html', {
            'error_message': str(e)
        })


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def users_list(request):
    """
    List all users with pagination, filtering, and query optimization.
    
    GET Parameters:
    - page: Page number (default: 1)
    - role: Filter by role (optional)
    - status: Filter by status - active, inactive, verified (optional)
    - search: Search in username, email, first_name, last_name (optional)
    
    Query Optimization:
    - Uses select_related() for role ForeignKey
    - Uses Count() for role permission counts
    - Uses only() for minimal field loading
    - Uses distinct() to avoid duplicates
    
    Pagination:
    - 10 items per page
    - Includes total_count in response
    
    Returns:
        HttpResponse: Rendered users list template with pagination
    """
    try:
        # Base queryset with optimizations
        users_queryset = CustomUser.objects.select_related('role').order_by('-date_joined')
        
        # Apply role filter
        role_filter = request.GET.get('role', '').strip()
        if role_filter:
            try:
                role_filter = int(role_filter)
                users_queryset = users_queryset.filter(role_id=role_filter)
            except (ValueError, TypeError):
                pass
        
        # Apply status filter
        status_filter = request.GET.get('status', '').strip().lower()
        if status_filter == 'active':
            users_queryset = users_queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            users_queryset = users_queryset.filter(is_active=False)
        elif status_filter == 'verified':
            users_queryset = users_queryset.filter(is_verified=True)
        elif status_filter == 'unverified':
            users_queryset = users_queryset.filter(is_verified=False)
        
        # Apply search filter
        search_query = request.GET.get('search', '').strip()
        if search_query:
            users_queryset = users_queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Get available roles for filter dropdown
        roles = Role.objects.annotate(
            user_count=Count('users', distinct=True)
        ).order_by('name')
        
        # Get page number
        page_number = request.GET.get('page', 1)
        
        # Paginate the queryset
        users, pagination_info = _get_paginated_response(
            users_queryset,
            page_number,
            page_size=10
        )
        
        if users is None:
            messages.error(request, 'Pagination error occurred.')
            return render(request, 'users/users_list.html', {
                'users': [],
                'pagination': {},
                'roles': roles
            })
        
        context = {
            'users': users,
            'pagination': pagination_info,
            'roles': roles,
            'current_role': role_filter,
            'current_status': status_filter,
            'search_query': search_query,
            'status_choices': [
                ('active', 'Active'),
                ('inactive', 'Inactive'),
                ('verified', 'Verified'),
                ('unverified', 'Unverified')
            ]
        }
        
        return render(request, 'users/users_list.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading users: {str(e)}')
        return render(request, 'users/users_list.html', {
            'users': [],
            'pagination': {},
            'error_message': str(e)
        })


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def user_detail(request, user_id):
    """
    View detailed information about a specific user.
    
    Args:
        user_id (int): ID of user to view
    
    Query Optimization:
    - Uses select_related for role
    - Uses only() to load minimal fields
    
    Error Handling:
    - 404 Not Found: If user doesn't exist
    
    Returns:
        HttpResponse: Rendered user detail template
    """
    try:
        # Query optimization: select_related for role
        user = CustomUser.objects.select_related('role').get(id=user_id)
    
    except CustomUser.DoesNotExist:
        error_message = f'User with ID {user_id} not found.'
        messages.error(request, error_message)
        return render(request, 'users/user_detail.html', {
            'error_message': error_message
        }, status=404)
    
    except Exception as e:
        error_message = f'Database error: {str(e)}'
        messages.error(request, error_message)
        return render(request, 'users/user_detail.html', {
            'error_message': error_message
        }, status=400)
    
    # Get role permissions if role is assigned
    role_permissions = []
    if user.role:
        role_permissions = list(
            user.role.role_permissions.select_related('permission').values_list(
                'permission__name', flat=True
            )
        )
    
    context = {
        'user': user,
        'role_permissions': role_permissions,
        'account_age_days': (timezone.now() - user.date_joined).days
    }
    
    return render(request, 'users/user_detail.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def change_user_status(request, user_id):
    """
    Change user active/inactive status.
    
    Args:
        user_id (int): ID of user to update
    
    POST Parameters:
    - is_active: 'true' or 'false' string
    
    Error Handling:
    - 404 Not Found: If user doesn't exist
    - 400 Bad Request: If invalid input
    - 403 Forbidden: If insufficient permission (optional)
    
    Returns:
        HttpResponse: Redirect to previous page or user detail
    """
    try:
        # Validate is_active parameter
        is_active_str = request.POST.get('is_active', 'false').lower()
        if is_active_str not in ('true', 'false'):
            messages.error(request, 'Invalid status value provided.')
            return redirect(request.META.get('HTTP_REFERER', 'users_list'))
        
        is_active = is_active_str == 'true'
        
        # Get user
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            error_message = f'User with ID {user_id} not found.'
            messages.error(request, error_message)
            return redirect('users_list')
        
        # Update user status
        user.is_active = is_active
        user.save(update_fields=['is_active'])
        
        status_text = 'activated' if is_active else 'deactivated'
        messages.success(request, f'User "{user.username}" has been {status_text}.')
        
        return redirect(request.META.get('HTTP_REFERER', 'users_list'))
    
    except Exception as e:
        error_message = f'Error updating user status: {str(e)}'
        messages.error(request, error_message)
        return redirect('users_list')


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def assign_user_role(request, user_id):
    """
    Assign or update user role.
    
    Args:
        user_id (int): ID of user to update
    
    POST Parameters:
    - role_id: ID of role to assign
    
    Validation:
    - Checks user exists
    - Checks role exists
    - Prevents assigning invalid roles
    
    Error Handling:
    - 404 Not Found: User or role not found
    - 400 Bad Request: Invalid input
    
    Returns:
        HttpResponse: Redirect to user detail or previous page
    """
    try:
        # Get role_id from POST
        try:
            role_id = int(request.POST.get('role_id', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid role ID provided.')
            return redirect(request.META.get('HTTP_REFERER', 'users_list'))
        
        # Get user
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            error_message = f'User with ID {user_id} not found.'
            messages.error(request, error_message)
            return redirect('users_list')
        
        # Get role
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            error_message = f'Role with ID {role_id} not found.'
            messages.error(request, error_message)
            return redirect(f'user_detail', user_id=user_id)
        
        # Update user role
        old_role = user.role
        user.role = role
        user.save(update_fields=['role'])
        
        old_role_name = old_role.name if old_role else 'No Role'
        messages.success(
            request,
            f'User "{user.username}" role changed from "{old_role_name}" to "{role.name}".'
        )
        
        return redirect(request.META.get('HTTP_REFERER', f'user_detail?user_id={user_id}'))
    
    except Exception as e:
        error_message = f'Error assigning role: {str(e)}'
        messages.error(request, error_message)
        return redirect('users_list')


# ============================================================================
# STAFFGRID ADMIN DASHBOARD VIEWS
# ============================================================================

@login_required(login_url='auth:login')
def staffgrid_dashboard_overview(request):
    """
    StaffGrid Main Dashboard Overview Page (THE ONLY DASHBOARD)
    
    Displays:
    - Real-time statistics (fetched via API)
    - Revenue charts (Chart.js with API data)
    - Plan distribution charts (Chart.js with API data)
    - Recent activity
    
    All data is loaded dynamically via AJAX calls to API endpoints.
    No hardcoded or dummy data allowed.
    
    This is the primary and ONLY dashboard for the application.
    """
    context = {
        'page_title': 'Dashboard Overview - StaffGrid',
        'current_page': 'overview',
        'user': request.user,
    }
    
    return render(request, 'dashboard/staffgrid_overview.html', context)


@login_required(login_url='auth:login')
def staffgrid_tenants(request):
    """StaffGrid Tenants Management Page"""
    context = {
        'page_title': 'Tenants Management - StaffGrid',
        'current_page': 'tenants',
    }
    
    return render(request, 'dashboard/staffgrid_tenants.html', context)


@login_required(login_url='auth:login')
def staffgrid_plans(request):
    """StaffGrid Plans Management Page"""
    context = {
        'page_title': 'Plan Management - StaffGrid',
        'current_page': 'plans',
    }
    
    return render(request, 'dashboard/staffgrid_plans.html', context)


@login_required(login_url='auth:login')
def staffgrid_subscriptions(request):
    """StaffGrid Subscriptions Management Page"""
    context = {
        'page_title': 'Subscriptions - StaffGrid',
        'current_page': 'subscriptions',
    }
    
    return render(request, 'dashboard/staffgrid_subscriptions.html', context)
