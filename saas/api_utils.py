"""
Validation utilities and helpers for production-ready API responses.

Provides:
- Input validation functions
- Error response builders
- Pagination helpers
- Query optimization utilities
"""

from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from typing import Tuple, Dict, Any, Optional, List


class APIResponse:
    """
    Standard API response builder for consistent error/success responses.
    
    Ensures all API responses follow the same structure:
    {
        'success': bool,
        'data': dict/list,
        'error_message': str (if error),
        'status': int
    }
    """
    
    @staticmethod
    def success(data: Any, status_code: int = 200, message: Optional[str] = None) -> JsonResponse:
        """
        Build successful API response.
        
        Args:
            data: Response data (dict, list, or object)
            status_code: HTTP status code (default: 200)
            message: Optional success message
        
        Returns:
            JsonResponse: Formatted success response
        """
        response_data = {
            'success': True,
            'data': data,
            'status': status_code
        }
        
        if message:
            response_data['message'] = message
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def error(error_message: str, status_code: int = 400) -> JsonResponse:
        """
        Build error API response.
        
        Args:
            error_message: Human-readable error message
            status_code: HTTP status code (default: 400)
        
        Returns:
            JsonResponse: Formatted error response
        """
        response_data = {
            'success': False,
            'error_message': error_message,
            'status': status_code
        }
        
        return JsonResponse(response_data, status=status_code)


class ValidationError:
    """
    Input validation helper with detailed error reporting.
    """
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
        
        Returns:
            tuple: (is_valid, error_message)
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                missing_fields.append(field)
        
        if missing_fields:
            error_message = f'Missing required fields: {", ".join(missing_fields)}'
            return False, error_message
        
        return True, None
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_value: Optional[int] = None,
                        max_value: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Validate that value is an integer within optional bounds.
        
        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
        
        Returns:
            tuple: (is_valid, error_message, converted_value)
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            error_message = f'{field_name} must be an integer.'
            return False, error_message, None
        
        if min_value is not None and int_value < min_value:
            error_message = f'{field_name} must be at least {min_value}.'
            return False, error_message, None
        
        if max_value is not None and int_value > max_value:
            error_message = f'{field_name} must be at most {max_value}.'
            return False, error_message, None
        
        return True, None, int_value
    
    @staticmethod
    def validate_string_length(value: str, field_name: str, min_length: Optional[int] = None,
                              max_length: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate string length within bounds.
        
        Args:
            value: String value to validate
            field_name: Field name for error messages
            min_length: Minimum allowed length (optional)
            max_length: Maximum allowed length (optional)
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(value, str):
            error_message = f'{field_name} must be a string.'
            return False, error_message
        
        if min_length is not None and len(value) < min_length:
            error_message = f'{field_name} must be at least {min_length} characters long.'
            return False, error_message
        
        if max_length is not None and len(value) > max_length:
            error_message = f'{field_name} must be at most {max_length} characters long.'
            return False, error_message
        
        return True, None
    
    @staticmethod
    def validate_choice(value: str, field_name: str, allowed_choices: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that value is one of allowed choices.
        
        Args:
            value: Value to validate
            field_name: Field name for error messages
            allowed_choices: List of allowed values
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if value not in allowed_choices:
            error_message = f'{field_name} must be one of: {", ".join(allowed_choices)}.'
            return False, error_message
        
        return True, None


class PaginationHelper:
    """
    Pagination utilities for consistent paginated responses.
    """
    
    DEFAULT_PAGE_SIZE = 10
    
    @staticmethod
    def paginate(queryset: QuerySet, page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> \
            Tuple[List[Any], Dict[str, Any], Optional[str]]:
        """
        Paginate a queryset and return results with pagination info.
        
        Args:
            queryset: Django ORM queryset to paginate
            page_number: Page number requested (default: 1)
            page_size: Items per page (default: 10)
        
        Returns:
            tuple: (items, pagination_info, error_message)
                - items: List of items for the current page
                - pagination_info: Dictionary with pagination metadata
                - error_message: None if successful, error string if failed
        """
        try:
            paginator = Paginator(queryset, page_size)
            
            try:
                page = paginator.page(page_number)
            except (EmptyPage, PageNotAnInteger):
                # Return first page if requested page is invalid
                page = paginator.page(1)
            
            pagination_info = {
                'current_page': page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'page_size': page_size,
                'has_next': page.has_next(),
                'has_previous': page.has_previous(),
                'next_page_number': page.next_page_number() if page.has_next() else None,
                'previous_page_number': page.previous_page_number() if page.has_previous() else None,
            }
            
            return list(page.object_list), pagination_info, None
        
        except Exception as e:
            error_message = f'Pagination error: {str(e)}'
            return [], {}, error_message
    
    @staticmethod
    def get_pagination_context(page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Dict[str, Any]:
        """
        Get pagination context object for template rendering.
        
        Args:
            page_number: Page number (default: 1)
            page_size: Items per page (default: 10)
        
        Returns:
            dict: Pagination context for templates
        """
        return {
            'page_size': page_size,
            'requested_page': page_number,
            'default_page_size': PaginationHelper.DEFAULT_PAGE_SIZE
        }


class QueryOptimizer:
    """
    Query optimization utilities for Django ORM.
    """
    
    @staticmethod
    def optimize_role_queryset(queryset: QuerySet) -> QuerySet:
        """
        Optimize role queryset with select_related and prefetch_related.
        
        Args:
            queryset: Base role queryset
        
        Returns:
            QuerySet: Optimized queryset
        """
        from django.db.models import Count, Prefetch
        
        # Import within function to avoid circular imports
        try:
            from saas.models import RolePermission
        except ImportError:
            # Fallback if import fails (will be caught in runtime)
            return queryset
        
        return queryset.prefetch_related(
            Prefetch(
                'role_permissions',
                queryset=RolePermission.objects.select_related('permission')
            )
        ).annotate(
            permission_count=Count('role_permissions', distinct=True),
            user_count=Count('users', distinct=True)
        )
    
    @staticmethod
    def optimize_user_queryset(queryset: QuerySet) -> QuerySet:
        """
        Optimize user queryset with select_related and prefetch_related.
        
        Args:
            queryset: Base user queryset
        
        Returns:
            QuerySet: Optimized queryset
        """
        return queryset.select_related('role').distinct()
    
    @staticmethod
    def optimize_permission_queryset(queryset: QuerySet) -> QuerySet:
        """
        Optimize permission queryset with select_related and prefetch_related.
        
        Args:
            queryset: Base permission queryset
        
        Returns:
            QuerySet: Optimized queryset
        """
        from django.db.models import Count, Prefetch
        
        # Import within function to avoid circular imports
        try:
            from saas.models import RolePermission
        except ImportError:
            # Fallback if import fails (will be caught in runtime)
            return queryset
        
        return queryset.prefetch_related(
            Prefetch(
                'permission_roles',
                queryset=RolePermission.objects.select_related('role')
            )
        ).annotate(
            role_count=Count('permission_roles', distinct=True)
        )


class ErrorHandler:
    """
    Centralized error handling with appropriate HTTP status codes.
    """
    
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_500_INTERNAL_ERROR = 500
    
    @staticmethod
    def handle_not_found(resource_name: str, resource_id: Any) -> JsonResponse:
        """
        Handle 404 Not Found errors.
        
        Args:
            resource_name: Name of the resource (e.g., 'User', 'Role')
            resource_id: ID of the resource
        
        Returns:
            JsonResponse: 404 error response
        """
        error_message = f'{resource_name} with ID {resource_id} not found.'
        return APIResponse.error(error_message, status_code=ErrorHandler.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def handle_unauthorized() -> JsonResponse:
        """
        Handle 401 Unauthorized errors.
        
        Returns:
            JsonResponse: 401 error response
        """
        error_message = 'User not authenticated. Please log in to continue.'
        return APIResponse.error(error_message, status_code=ErrorHandler.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def handle_forbidden() -> JsonResponse:
        """
        Handle 403 Forbidden errors.
        
        Returns:
            JsonResponse: 403 error response
        """
        error_message = 'User lacks permission to perform this action.'
        return APIResponse.error(error_message, status_code=ErrorHandler.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def handle_bad_request(error_message: str) -> JsonResponse:
        """
        Handle 400 Bad Request errors.
        
        Args:
            error_message: Detailed error message
        
        Returns:
            JsonResponse: 400 error response
        """
        return APIResponse.error(error_message, status_code=ErrorHandler.HTTP_400_BAD_REQUEST)
    
    @staticmethod
    def handle_server_error(error_message: str) -> JsonResponse:
        """
        Handle 500 Internal Server Error.
        
        Args:
            error_message: Detailed error message
        
        Returns:
            JsonResponse: 500 error response
        """
        return APIResponse.error(error_message, status_code=ErrorHandler.HTTP_500_INTERNAL_ERROR)
