"""
Utility functions for SaaS application
"""
from django.shortcuts import redirect
from django.contrib import messages


def get_user_dashboard_url(user):
    """
    Determine the appropriate dashboard URL based on user role and subscription status.
    
    Returns:
        str: URL path to redirect user to
    """
    # 1. SUPER_ADMIN (staff/superuser) -> SaaS Admin Dashboard
    if user.is_superuser or user.is_staff:
        return '/saas-admin/dashboard/'
    
    # 2. Get user's tenant
    tenant = getattr(user, 'tenant', None)
    
    if not tenant:
        # User has no tenant - should not happen, but redirect to landing
        return '/'
    
    # 3. Check user's role
    role = getattr(user, 'role', None)
    role_name = role.name.upper() if role and role.name else None
    
    # 4. COMPANY_ADMIN (tenant owner or admin)
    if role_name in ['COMPANY_ADMIN', 'ADMIN', 'OWNER']:
        # Check if tenant has active subscription
        from .models import Subscription
        subscription = Subscription.objects.filter(
            tenant=tenant, 
            status='active'
        ).order_by('-created_at').first()
        
        if not subscription:
            # No active subscription - redirect to pricing page
            return '/billing/pricing/'
        
        # Has active subscription - redirect to HRM dashboard
        return '/hrm/overview/'
    
    # 5. EMPLOYEE - always to HRM dashboard (if company has subscription)
    elif role_name == 'EMPLOYEE':
        return '/hrm/overview/'
    
    # 6. Default - redirect to HRM dashboard
    return '/hrm/overview/'


def check_subscription_access(user):
    """
    Check if user has access to HRM features based on subscription.
    
    Returns:
        tuple: (has_access: bool, message: str, redirect_url: str)
    """
    # Super admin always has access
    if user.is_superuser or user.is_staff:
        return True, None, None
    
    # Get user's tenant
    tenant = getattr(user, 'tenant', None)
    
    if not tenant:
        return False, "You are not associated with any company.", "/"
    
    # Check for active subscription
    subscription = tenant.subscriptions.filter(status='active').order_by('-created_at').first()
    
    if not subscription:
        return False, "Your company does not have an active subscription plan. Please subscribe to access HRM features.", "/billing/pricing/"
    
    # Check if subscription is expired
    from django.utils import timezone
    if subscription.end_date and timezone.now().date() > subscription.end_date:
        subscription.status = 'expired'
        subscription.save()
        return False, "Your subscription has expired. Please renew to continue using HRM features.", "/billing/pricing/"
    
    return True, None, None
