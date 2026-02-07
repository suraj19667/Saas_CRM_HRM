"""
Subscription Validation Middleware

This middleware protects HRM routes and ensures:
1. Only authenticated users can access HRM
2. Only users with active subscriptions can access HRM (except super admins)
3. COMPANY_ADMIN without subscription is redirected to pricing page
4. EMPLOYEE can only access HRM if their company has active subscription
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SubscriptionValidationMiddleware:
    """
    Middleware to validate subscription before allowing access to HRM routes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # HRM routes that require subscription
        self.protected_hrm_routes = [
            '/hrm/',
        ]
        
        # Routes that don't require subscription check
        self.exempt_routes = [
            '/auth/',
            '/billing/',
            '/saas-admin/',
            '/admin/',
            '/static/',
            '/media/',
            '/api/',
            '/',
            '/landing/',
            '/logout/',
            '/login/',
            '/register/',
            '/company/',
        ]
    
    def __call__(self, request):
        # Check if this is an HRM route
        is_hrm_route = any(request.path.startswith(route) for route in self.protected_hrm_routes)
        
        if is_hrm_route:
            # Allow if user is not authenticated (will be handled by @login_required)
            if not request.user.is_authenticated:
                return self.get_response(request)
            
            # Allow super admin and staff
            if request.user.is_superuser or request.user.is_staff:
                return self.get_response(request)
            
            # Check user's tenant
            tenant = getattr(request.user, 'tenant', None)
            
            if not tenant:
                messages.error(request, 'You are not associated with any company.')
                logger.warning(f'User {request.user.email} tried to access HRM without tenant')
                return redirect('/')
            
            # Check for active subscription
            from saas.models import Subscription
            subscription = Subscription.objects.filter(
                tenant=tenant, 
                status='active'
            ).order_by('-created_at').first()
            
            if not subscription:
                messages.warning(
                    request, 
                    'Your company does not have an active subscription. Please subscribe to access HRM features.'
                )
                logger.info(f'User {request.user.email} blocked from HRM - no active subscription')
                return redirect('/billing/pricing/')
            
            # Check if subscription is expired
            if subscription.end_date and timezone.now().date() > subscription.end_date:
                subscription.status = 'expired'
                subscription.save()
                messages.error(
                    request, 
                    'Your subscription has expired. Please renew to continue using HRM features.'
                )
                logger.info(f'User {request.user.email} blocked from HRM - subscription expired')
                return redirect('/billing/pricing/')
        
        response = self.get_response(request)
        return response
