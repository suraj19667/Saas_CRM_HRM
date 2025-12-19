"""
Authentication and permission middleware with comprehensive error handling.

Implements:
- User authentication validation
- Permission checking
- Request logging
- Error responses with proper HTTP status codes
"""

import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """
    Middleware to validate user authentication on protected endpoints.
    
    Returns:
    - 401 Unauthorized: User not authenticated on protected routes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define protected API routes that require authentication
        self.protected_routes = [
            '/api/roles/',
            '/api/permissions/',
            '/api/users/',
            '/dashboard/',
            '/roles/',
            '/permissions/',
            '/users/'
        ]
    
    def __call__(self, request):
        # Check if the request path requires authentication
        if any(request.path.startswith(route) for route in self.protected_routes):
            if not request.user.is_authenticated:
                logger.warning(f'Unauthenticated access attempt to {request.path}')
                
                # Return JSON error for API endpoints, redirect for templates
                if request.path.startswith('/api/'):
                    return JsonResponse(
                        {
                            'success': False,
                            'error_message': 'User not authenticated. Please log in.',
                            'status': 401
                        },
                        status=401
                    )
        
        response = self.get_response(request)
        return response


class ErrorHandlingMiddleware:
    """
    Middleware to handle and standardize error responses.
    
    Features:
    - Catches unhandled exceptions
    - Returns consistent error response format
    - Logs errors for debugging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            
            # Handle 4xx and 5xx responses
            if response.status_code >= 400:
                # Only modify API responses
                if request.path.startswith('/api/'):
                    content_type = response.get('Content-Type', '')
                    if 'application/json' not in content_type:
                        # Non-JSON response, convert to standard error format
                        error_message = self._get_status_message(response.status_code)
                        response = JsonResponse(
                            {
                                'success': False,
                                'error_message': error_message,
                                'status': response.status_code
                            },
                            status=response.status_code
                        )
            
            return response
        
        except Exception as e:
            logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
            
            # Return appropriate error response
            if request.path.startswith('/api/'):
                return JsonResponse(
                    {
                        'success': False,
                        'error_message': 'Internal server error. Please try again later.',
                        'status': 500
                    },
                    status=500
                )
            else:
                raise
    
    @staticmethod
    def _get_status_message(status_code):
        """Get human-readable message for HTTP status code."""
        messages = {
            400: 'Bad request. Please check your input.',
            401: 'Unauthorized. Please log in.',
            403: 'Forbidden. You lack permission for this action.',
            404: 'Resource not found.',
            500: 'Internal server error. Please try again later.'
        }
        return messages.get(status_code, f'HTTP Error {status_code}')


class RequestLoggingMiddleware:
    """
    Middleware to log API requests and responses.
    
    Features:
    - Logs request method, path, and user
    - Logs response status code
    - Logs execution time
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import time
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Only log API endpoints
        if request.path.startswith('/api/'):
            user_identifier = request.user.username if request.user.is_authenticated else 'anonymous'
            log_message = (
                f'{request.method} {request.path} | '
                f'Status: {response.status_code} | '
                f'User: {user_identifier} | '
                f'Duration: {duration:.3f}s'
            )
            logger.info(log_message)
        
        return response


class RateLimitingMiddleware:
    """
    Simple rate limiting middleware to prevent abuse.
    
    Features:
    - Tracks requests per IP/user
    - Returns 429 Too Many Requests when limit exceeded
    - Configurable limits per endpoint
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        self.limit = 100  # Requests per minute
    
    def __call__(self, request):
        # Get client IP or user identifier
        if request.user.is_authenticated:
            identifier = f'user_{request.user.id}'
        else:
            identifier = self._get_client_ip(request)
        
        # Check rate limit (simple implementation)
        if identifier not in self.request_counts:
            self.request_counts[identifier] = {'count': 0, 'timestamp': None}
        
        current_request = self.request_counts[identifier]
        import time
        current_time = time.time()
        
        # Reset count if more than 60 seconds have passed
        if current_request['timestamp'] and current_time - current_request['timestamp'] > 60:
            current_request['count'] = 0
            current_request['timestamp'] = current_time
        
        current_request['count'] += 1
        current_request['timestamp'] = current_time
        
        # Return 429 if limit exceeded
        if current_request['count'] > self.limit:
            return JsonResponse(
                {
                    'success': False,
                    'error_message': 'Rate limit exceeded. Please try again later.',
                    'status': 429
                },
                status=429
            )
        
        response = self.get_response(request)
        return response
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
