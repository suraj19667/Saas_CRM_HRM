"""
REST API views for feature management.

Provides JSON API endpoints for CRUD operations on features.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json
import logging

from .models import Feature
from .api_utils import APIResponse, ErrorHandler, ValidationError, PaginationHelper

logger = logging.getLogger(__name__)


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def list_features(request):
    """
    API endpoint to list all features.
    
    GET Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    - search: Search query for feature name
    
    Returns:
        JsonResponse with paginated feature list
    """
    try:
        search_query = request.GET.get('search', '').strip()
        page_number, page_size = PaginationHelper.get_pagination_params(request)
        
        # Get queryset
        queryset = Feature.objects.all().select_related('module').order_by('-created_at')
        
        # Apply search filter
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        # Paginate
        items, current_page, total_pages, total_count = PaginationHelper.paginate(
            queryset, page_number, page_size
        )
        
        # Serialize data
        features_data = [
            {
                'id': feature.id,
                'name': feature.name,
                'description': feature.description or '',
                'module': feature.module.name if feature.module else None,
                'is_active': feature.is_active,
                'created_at': feature.created_at.isoformat(),
            }
            for feature in items
        ]
        
        return APIResponse.paginated(
            features_data,
            current_page,
            total_count,
            int(page_size),
            "Features retrieved successfully"
        )
    
    except Exception as e:
        return ErrorHandler.handle_server_error(e, "Failed to retrieve features")


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def get_feature(request, feature_id):
    """
    API endpoint to get a specific feature.
    
    Args:
        feature_id: ID of the feature to retrieve
    
    Returns:
        JsonResponse with feature details
    """
    try:
        feature = get_object_or_404(Feature, id=feature_id)
        
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description or '',
            'module': feature.module.name if feature.module else None,
            'is_active': feature.is_active,
            'created_at': feature.created_at.isoformat(),
            'updated_at': feature.updated_at.isoformat() if hasattr(feature, 'updated_at') else None,
        }
        
        return APIResponse.success(feature_data, "Feature retrieved successfully")
    
    except Feature.DoesNotExist:
        return ErrorHandler.handle_not_found("Feature not found")
    except Exception as e:
        return ErrorHandler.handle_server_error(e, "Failed to retrieve feature")


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
@csrf_exempt
def create_feature(request):
    """
    API endpoint to create a new feature.
    
    POST Parameters (JSON):
    - name: Feature name (required)
    - description: Feature description (optional)
    - module_id: Module ID (optional)
    - is_active: Whether feature is active (optional, default: true)
    
    Returns:
        JsonResponse with created feature details
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('name'):
            raise ValidationError("Feature name is required", field='name')
        
        # Check for duplicates
        if Feature.objects.filter(name=data['name']).exists():
            raise ValidationError("Feature with this name already exists", field='name')
        
        # Create feature
        feature = Feature.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
        if data.get('module_id'):
            from .models import Module
            try:
                module = Module.objects.get(id=data['module_id'])
                feature.module = module
                feature.save()
            except Module.DoesNotExist:
                pass
        
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description or '',
            'module': feature.module.name if feature.module else None,
            'is_active': feature.is_active,
            'created_at': feature.created_at.isoformat(),
        }
        
        return APIResponse.success(feature_data, "Feature created successfully", status_code=201)
    
    except ValidationError as e:
        return ErrorHandler.handle_validation_error(e)
    except json.JSONDecodeError:
        return APIResponse.error("Invalid JSON in request body", status_code=400)
    except Exception as e:
        return ErrorHandler.handle_server_error(e, "Failed to create feature")


@login_required(login_url='auth:login')
@require_http_methods(['PUT'])
@csrf_exempt
def update_feature(request, feature_id):
    """
    API endpoint to update a feature.
    
    PUT Parameters (JSON):
    - name: Feature name (optional)
    - description: Feature description (optional)
    - module_id: Module ID (optional)
    - is_active: Whether feature is active (optional)
    
    Returns:
        JsonResponse with updated feature details
    """
    try:
        feature = get_object_or_404(Feature, id=feature_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'name' in data:
            if Feature.objects.filter(name=data['name']).exclude(id=feature_id).exists():
                raise ValidationError("Feature with this name already exists", field='name')
            feature.name = data['name']
        
        if 'description' in data:
            feature.description = data['description']
        
        if 'is_active' in data:
            feature.is_active = data['is_active']
        
        if 'module_id' in data and data['module_id']:
            from .models import Module
            try:
                module = Module.objects.get(id=data['module_id'])
                feature.module = module
            except Module.DoesNotExist:
                pass
        
        feature.save()
        
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description or '',
            'module': feature.module.name if feature.module else None,
            'is_active': feature.is_active,
            'created_at': feature.created_at.isoformat(),
            'updated_at': feature.updated_at.isoformat() if hasattr(feature, 'updated_at') else None,
        }
        
        return APIResponse.success(feature_data, "Feature updated successfully")
    
    except Feature.DoesNotExist:
        return ErrorHandler.handle_not_found("Feature not found")
    except ValidationError as e:
        return ErrorHandler.handle_validation_error(e)
    except json.JSONDecodeError:
        return APIResponse.error("Invalid JSON in request body", status_code=400)
    except Exception as e:
        return ErrorHandler.handle_server_error(e, "Failed to update feature")


@login_required(login_url='auth:login')
@require_http_methods(['DELETE'])
@csrf_exempt
def delete_feature(request, feature_id):
    """
    API endpoint to delete a feature.
    
    Args:
        feature_id: ID of the feature to delete
    
    Returns:
        JsonResponse with success/failure message
    """
    try:
        feature = get_object_or_404(Feature, id=feature_id)
        feature_name = feature.name
        feature.delete()
        
        return APIResponse.success(
            {'deleted_id': feature_id},
            f"Feature '{feature_name}' deleted successfully"
        )
    
    except Feature.DoesNotExist:
        return ErrorHandler.handle_not_found("Feature not found")
    except Exception as e:
        return ErrorHandler.handle_server_error(e, "Failed to delete feature")
