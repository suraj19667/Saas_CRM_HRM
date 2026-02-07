"""
Custom middleware for HRM routing and redirection
"""
from django.shortcuts import redirect
from django.urls import reverse


class HRMRoutingMiddleware:
    """
    Middleware to route users to appropriate dashboards after login
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process authenticated users
        if request.user.is_authenticated:
            # Check if user is accessing root dashboard URL
            if request.path == '/dashboard/' or request.path == '/dashboard/overview/':
                # If user is staff/superuser, allow access to admin dashboard
                if request.user.is_staff or request.user.is_superuser:
                    pass  # Continue to admin dashboard
                else:
                    # Regular users (HRM customers) go to HRM dashboard
                    return redirect('hrm_overview')
        
        response = self.get_response(request)
        return response
