from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from saas.models.tenant import Tenant
from saas.models.subscription import Subscription
from datetime import date

class NoCacheMiddleware:
    """
    Middleware to prevent caching of authenticated pages
    Adds no-cache headers to protected routes for better security
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Cache the URL patterns to avoid repeated reverse() calls
        self.protected_paths = []
        
    def _get_protected_paths(self):
        """Lazy load protected paths only once"""
        if not self.protected_paths:
            try:
                self.protected_paths = [
                    reverse('dashboard'),
                    reverse('logout'),
                    reverse('leads'),
                    reverse('deals'),
                    reverse('form_builder'),
                    reverse('contract'),
                    reverse('crm_setup'),
                ]
            except Exception:
                # If URLs are not ready yet, return empty list
                self.protected_paths = []
        return self.protected_paths

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add aggressive no-cache headers to ALL pages (public + protected) to prevent back button issues
        protected_paths = self._get_protected_paths()
        public_paths = [
            '/auth/login/',
            '/auth/register/',
        ]
        
        if request.path in protected_paths or request.path in public_paths:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            # Additional headers to prevent back button caching
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
            # Force page reload on back button
            response['Clear-Site-Data'] = '"cache"'
        
        return response


class LoginRequiredMiddleware:
    """
    Global middleware to enforce authentication on protected routes
    Works as a backup to @login_required decorator
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that don't require authentication
        self.public_paths = []
        self.protected_paths = []
        
    def _get_public_paths(self):
        """Get list of public URLs that don't require authentication"""
        if not self.public_paths:
            try:
                self.public_paths = [
                    reverse('auth:login'),
                    reverse('auth:register'),
                    reverse('verify_otp'),
                    reverse('resend_otp'),
                ]
            except Exception:
                self.public_paths = []
        return self.public_paths
    
    def _get_protected_paths(self):
        """Get list of protected URLs that require authentication"""
        if not self.protected_paths:
            try:
                self.protected_paths = [
                    reverse('dashboard'),
                    reverse('leads'),
                    reverse('deals'),
                    reverse('form_builder'),
                    reverse('contract'),
                    reverse('crm_setup'),
                    reverse('subscription:list_plans'),
                ]
            except Exception:
                self.protected_paths = []
        return self.protected_paths

    def __call__(self, request):
        # Allow static files and admin routes
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # If user is authenticated and trying to access login/register pages
        # Redirect them to dashboard (prevent back button to login after login)
        if request.user.is_authenticated and request.path in self._get_public_paths():
            from django.urls import reverse
            response = redirect(reverse(settings.LOGIN_REDIRECT_URL))
            # Add no-cache headers to redirect response
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        # Check if user is trying to access protected routes without authentication
        if request.path in self._get_protected_paths():
            if not request.user.is_authenticated:
                response = redirect('auth:login')
                # Add no-cache headers to redirect response
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
        
        response = self.get_response(request)
        return response


class SubscriptionMiddleware:
    """
    Middleware to check active subscription for authenticated users
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/auth/',
            '/admin/',
            '/static/',
            '/media/',
            '/logout/',
            '/subscription/',  # Allow access to subscription pages
            '/plans/',  # Allow super admins to manage plans
        ]

    def __call__(self, request):
        # Skip for unauthenticated users or exempt paths
        if not request.user.is_authenticated or any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)

        # Skip for superusers (admins can access everything)
        if request.user.is_superuser:
            return self.get_response(request)

        # Check if user has a tenant
        tenant = request.user.tenant
        if not tenant:
            # User doesn't have a tenant, allow access (maybe they are just a user)
            return self.get_response(request)

        # Check for active subscription
        active_subscription = Subscription.objects.filter(
            tenant=tenant,
            status='active',
            end_date__gte=date.today()
        ).first()

        if not active_subscription:
            messages.warning(request, 'You need an active subscription to access premium features. <a href="/subscriptions/">Subscribe now</a>')
            # Do not redirect, just show message on current page
        request.subscription = active_subscription

        response = self.get_response(request)
        return response


from .tenant_middleware import TenantMiddleware, FeatureAccessMiddleware
