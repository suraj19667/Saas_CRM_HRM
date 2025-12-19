from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.timezone import now
from ..models import Tenant


class TenantMiddleware:
    """Middleware to validate tenant access and subscription"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path_parts = request.path.split('/')
        if len(path_parts) > 1:
            tenant_slug = path_parts[1]
            try:
                tenant = Tenant.objects.get(slug=tenant_slug)
                if not tenant.is_subscription_active:
                    return redirect("subscription_plans")
                request.tenant = tenant
            except Tenant.DoesNotExist:
                pass

        response = self.get_response(request)
        return response

    def get_subdomain(self, host):
        """Extract subdomain from host"""
        # Remove port
        domain = host.split(':')[0]
        parts = domain.split('.')
        
        # Skip localhost and IP addresses
        if domain in ['localhost', '127.0.0.1'] or (len(parts) == 4 and all(p.isdigit() for p in parts[:3])):
            return None
        
        if len(parts) > 2:
            # e.g., company1.mini-saas.local -> company1
            return parts[0]
        return None


class FeatureAccessMiddleware:
    """Middleware to check feature access based on subscription"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # This would be used to check specific features
        # For now, just pass through
        response = self.get_response(request)
        return response