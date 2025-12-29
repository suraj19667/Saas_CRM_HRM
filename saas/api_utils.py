"""
API utility classes and functions for REST endpoints.

Provides common utilities for API responses, error handling, pagination, and validation.
"""

from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """Helper class for standardized API responses."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> JsonResponse:
        """Return a successful API response."""
        response_data = {
            'success': True,
            'message': message,
        }
        if data is not None:
            response_data['data'] = data
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def error(message: str, error_code: Optional[str] = None, status_code: int = 400, data: Any = None) -> JsonResponse:
        """Return an error API response."""
        response_data = {
            'success': False,
            'message': message,
        }
        if error_code:
            response_data['error_code'] = error_code
        if data is not None:
            response_data['data'] = data
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def paginated(items: List[Dict], page_number: int, total_count: int, page_size: int, message: str = "Success") -> JsonResponse:
        """Return a paginated API response."""
        from math import ceil
        total_pages = ceil(total_count / page_size) if page_size > 0 else 1
        
        response_data = {
            'success': True,
            'message': message,
            'data': {
                'items': items,
                'pagination': {
                    'current_page': page_number,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'page_size': page_size,
                }
            }
        }
        return JsonResponse(response_data, status=200)


class ValidationError(Exception):
    """Custom validation error for API validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, status_code: int = 400):
        self.message = message
        self.field = field
        self.status_code = status_code
        super().__init__(self.message)


class PaginationHelper:
    """Helper class for pagination logic."""
    
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    @staticmethod
    def paginate(queryset, page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE):
        """
        Paginate a queryset.
        
        Args:
            queryset: Django queryset to paginate
            page_number: Page number (default: 1)
            page_size: Items per page (default: 10, max: 100)
        
        Returns:
            tuple: (items, current_page, total_pages, total_count)
        """
        # Validate and normalize page_size
        try:
            page_size = int(page_size)
            if page_size <= 0:
                page_size = PaginationHelper.DEFAULT_PAGE_SIZE
            elif page_size > PaginationHelper.MAX_PAGE_SIZE:
                page_size = PaginationHelper.MAX_PAGE_SIZE
        except (ValueError, TypeError):
            page_size = PaginationHelper.DEFAULT_PAGE_SIZE
        
        paginator = Paginator(queryset, page_size)
        
        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 1
        
        try:
            page = paginator.page(page_number)
            items = page.object_list
            current_page = page.number
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
            items = page.object_list
            current_page = 1
        
        return items, current_page, paginator.num_pages, paginator.count
    
    @staticmethod
    def get_pagination_params(request):
        """Extract pagination parameters from request."""
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', PaginationHelper.DEFAULT_PAGE_SIZE)
        return page_number, page_size


class ErrorHandler:
    """Helper class for error handling and logging."""
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> JsonResponse:
        """Handle validation errors."""
        data = None
        if error.field:
            data = {error.field: error.message}
        return APIResponse.error(error.message, error_code='VALIDATION_ERROR', status_code=error.status_code, data=data)
    
    @staticmethod
    def handle_not_found(message: str = "Resource not found") -> JsonResponse:
        """Handle not found errors."""
        return APIResponse.error(message, error_code='NOT_FOUND', status_code=404)
    
    @staticmethod
    def handle_permission_denied(message: str = "Permission denied") -> JsonResponse:
        """Handle permission denied errors."""
        return APIResponse.error(message, error_code='PERMISSION_DENIED', status_code=403)
    
    @staticmethod
    def handle_unauthorized(message: str = "Unauthorized") -> JsonResponse:
        """Handle unauthorized errors."""
        return APIResponse.error(message, error_code='UNAUTHORIZED', status_code=401)
    
    @staticmethod
    def handle_server_error(exception: Exception, message: str = "An error occurred") -> JsonResponse:
        """Handle server errors and log them."""
        logger.error(f"Server error: {str(exception)}", exc_info=True)
        return APIResponse.error(message, error_code='SERVER_ERROR', status_code=500)
