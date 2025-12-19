"""
Custom authentication and permission decorators for role-based access control.

Features:
- @login_required_custom: Enhanced login requirement with permission checks
- @permission_required: Check if user has specific permission
- @role_required: Check if user has specific role
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import CompanySubscription


def permission_required(permission_codename, raise_exception=False):
    """
    Decorator to check if user has specific permission via their role.
    
    Usage:
        @permission_required('view_dashboard')
        def my_view(request):
            pass
    
    Args:
        permission_codename (str): The permission codename to check
        raise_exception (bool): If True, return 403. If False, redirect to login
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if raise_exception:
                    return JsonResponse(
                        {'error': 'User not authenticated'},
                        status=401
                    )
                return redirect(f"{reverse('auth:login')}?next={request.path}")
            
            # Check if user has permission
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            if request.user.has_permission(permission_codename):
                return view_func(request, *args, **kwargs)
            
            # Permission denied
            if raise_exception:
                return JsonResponse(
                    {'error': f'Permission denied: {permission_codename}'},
                    status=403
                )
            
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('tenant:dashboard')
        
        return wrapper
    return decorator


def role_required(*role_names):
    """
    Decorator to check if user has one of the specified roles.
    
    Usage:
        @role_required('admin', 'editor')
        def my_view(request):
            pass
    
    Args:
        role_names: One or more role names to check
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('auth:login')}?next={request.path}")
            
            # Superuser and staff always have access
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            # Check if user's role is in the allowed roles
            if request.user.role and request.user.role.name.lower() in [r.lower() for r in role_names]:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have the required role to access this page.')
            return redirect('tenant:dashboard')
        
        return wrapper
    return decorator


def multiple_permissions_required(*permission_codenames, logic='all'):
    """
    Decorator to check if user has multiple permissions.
    
    Usage:
        @multiple_permissions_required('view_users', 'edit_users', logic='all')
        def my_view(request):
            pass
    
    Args:
        permission_codenames: Permission codenamed to check
        logic: 'all' requires all permissions, 'any' requires at least one
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('auth:login')}?next={request.path}")
            
            # Superuser and staff always have access
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            # Check permissions based on logic
            if logic == 'all':
                has_permission = all(
                    request.user.has_permission(codename)
                    for codename in permission_codenames
                )
            else:  # logic == 'any'
                has_permission = any(
                    request.user.has_permission(codename)
                    for codename in permission_codenames
                )
            
            if has_permission:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have the required permissions.')
            return redirect('dashboard:dashboard')
        
        return wrapper
    return decorator


def login_required_custom(view_func):
    """
    Enhanced login_required with permission checks and JSON response support.
    
    Usage:
        @login_required_custom
        def my_view(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'error': 'Not authenticated'},
                    status=401
                )
            return redirect(f"{reverse('auth:login')}?next={request.path}")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_subscription_feature(feature_name):
    """
    Decorator to check if the tenant has access to a specific feature
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get tenant from session or URL
            tenant_slug = request.session.get('tenant_slug') or kwargs.get('tenant_slug')
            if not tenant_slug:
                messages.error(request, 'No tenant session found.')
                return redirect('company:login')

            try:
                # Get the user's tenant
                tenant = request.user.owned_tenants.get(slug=tenant_slug)
                subscription = CompanySubscription.objects.get(
                    tenant=tenant,
                    status='active'
                )

                if not subscription.is_active():
                    messages.warning(request, 'Your subscription has expired. Please renew to access this feature.')
                    return redirect('company:subscription_plans')

                # Check feature access
                plan_features = subscription.plan.features
                if isinstance(plan_features, str):
                    import json
                    plan_features = json.loads(plan_features)

                if feature_name not in plan_features or not plan_features[feature_name]:
                    messages.warning(request, f'This feature is not available in your current plan. Please upgrade.')
                    return redirect('tenant:dashboard')
                request.tenant = tenant
                request.subscription = subscription
                request.plan_features = plan_features

                return view_func(request, *args, **kwargs)

            except Exception as e:
                messages.error(request, 'Access denied.')
                return redirect('company:login')

        return _wrapped_view
    return decorator
