"""
Dashboard Protection Middleware

Ensures proper separation between:
1. SaaS Admin Dashboard (/saas-admin/*) - Only for SUPER_ADMIN
2. HRM Dashboard (/hrm/*) - Only for COMPANY_ADMIN and EMPLOYEE with active subscription
3. Prevents cross-access and enforces role-based routing
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class DashboardProtectionMiddleware:
    """
    Middleware to protect dashboards and enforce proper access control
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        path = request.path
        
        # Skip for non-authenticated users (handled by @login_required)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # ==================== SAAS ADMIN PROTECTION ====================
        # /saas-admin/* routes are ONLY for SUPER_ADMIN (superuser/staff)
        if path.startswith('/saas-admin/'):
            if not (request.user.is_superuser or request.user.is_staff):
                messages.error(request, 'Access denied. SaaS Admin dashboard is only for super administrators.')
                logger.warning(f'Non-admin user {request.user.email} attempted to access {path}')
                return redirect('/')
            
            # SUPER_ADMIN has access - continue
            return self.get_response(request)
        
        # ==================== HRM PROTECTION ====================
        # /hrm/* routes are ONLY for company users (COMPANY_ADMIN, EMPLOYEE)
        if path.startswith('/hrm/'):
            # 1. Block SUPER_ADMIN from accessing HRM
            if request.user.is_superuser or request.user.is_staff:
                messages.warning(request, 'Super administrators cannot access HRM dashboard. Use SaaS Admin dashboard instead.')
                logger.info(f'Super admin {request.user.email} redirected from HRM to SaaS Admin')
                return redirect('/saas-admin/dashboard/')
            
            # 2. Check if user has a tenant (company)
            tenant = getattr(request.user, 'tenant', None)
            if not tenant:
                messages.error(request, 'You are not associated with any company.')
                return redirect('/')
            
            # 3. Check if user's company has active subscription
            from saas.models import Subscription
            
            subscription = Subscription.objects.filter(
                tenant=tenant,
                status='active'
            ).order_by('-created_at').first()
            
            if not subscription:
                # No active subscription
                role = getattr(request.user, 'role', None)
                role_name = role.name.upper() if role and role.name else None
                
                # If user is COMPANY_ADMIN, redirect to pricing
                if role_name in ['COMPANY_ADMIN', 'ADMIN', 'OWNER']:
                    messages.warning(
                        request, 
                        'Your company does not have an active subscription. Please choose a plan to access HRM features.'
                    )
                    return redirect('/billing/pricing/')
                else:
                    # Employee - inform them to contact admin
                    messages.error(
                        request,
                        'Your company does not have an active subscription. Please contact your administrator.'
                    )
                    return redirect('/')
            
            # 4. Check if subscription is expired
            if subscription.end_date and timezone.now().date() > subscription.end_date:
                subscription.status = 'expired'
                subscription.save()
                
                messages.error(
                    request,
                    'Your company subscription has expired. Please renew to continue using HRM features.'
                )
                
                # Redirect admin to pricing, others to home
                role = getattr(request.user, 'role', None)
                role_name = role.name.upper() if role and role.name else None
                
                if role_name in ['COMPANY_ADMIN', 'ADMIN', 'OWNER']:
                    return redirect('/billing/pricing/')
                else:
                    return redirect('/')
            
            # User has valid subscription - allow access
            return self.get_response(request)
        
        # ==================== ROOT DASHBOARD REDIRECT ====================
        # Handle legacy /dashboard/ URLs
        if path in ['/dashboard/', '/dashboard/overview/']:
            if request.user.is_superuser or request.user.is_staff:
                return redirect('/saas-admin/dashboard/')
            else:
                return redirect('/hrm/overview/')
        
        # All other routes - continue normally
        return self.get_response(request)
