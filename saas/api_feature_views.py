"""
Feature API views for dashboard management
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Feature


@login_required
@require_http_methods(['GET'])
def get_feature(request, feature_id):
    """Get single feature data"""
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    feature = get_object_or_404(Feature, id=feature_id)
    
    return JsonResponse({
        'id': feature.id,
        'name': feature.name,
        'key': feature.key,
        'description': feature.description or '',
        'created_at': feature.created_at.isoformat(),
        'updated_at': feature.updated_at.isoformat(),
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def create_feature(request):
    """Create new feature"""
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        name = request.POST.get('name', '').strip()
        key = request.POST.get('key', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name or not key:
            return JsonResponse({'error': 'Name and key are required'}, status=400)
        
        # Check if key already exists
        if Feature.objects.filter(key=key).exists():
            return JsonResponse({'error': 'Feature key already exists'}, status=400)
        
        feature = Feature.objects.create(
            name=name,
            key=key,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Feature "{feature.name}" created successfully!',
            'feature': {
                'id': feature.id,
                'name': feature.name,
                'key': feature.key,
                'description': feature.description,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(['PUT', 'PATCH'])
def update_feature(request, feature_id):
    """Update existing feature"""
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        feature = get_object_or_404(Feature, id=feature_id)
        
        # Parse PUT data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        name = data.get('name', feature.name).strip()
        key = data.get('key', feature.key).strip()
        description = data.get('description', feature.description or '').strip()
        
        if not name or not key:
            return JsonResponse({'error': 'Name and key are required'}, status=400)
        
        # Check if key already exists (excluding current feature)
        if Feature.objects.filter(key=key).exclude(id=feature_id).exists():
            return JsonResponse({'error': 'Feature key already exists'}, status=400)
        
        feature.name = name
        feature.key = key
        feature.description = description
        feature.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Feature "{feature.name}" updated successfully!',
            'feature': {
                'id': feature.id,
                'name': feature.name,
                'key': feature.key,
                'description': feature.description,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(['DELETE'])
def delete_feature(request, feature_id):
    """Delete feature"""
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        feature = get_object_or_404(Feature, id=feature_id)
        
        # Check if feature is used in any plans
        if feature.plan_features.exists():
            return JsonResponse({
                'error': f'Cannot delete feature "{feature.name}" as it is used in {feature.plan_features.count()} plans'
            }, status=400)
        
        feature_name = feature.name
        feature.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Feature "{feature_name}" deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['GET'])
def list_features(request):
    """List all features"""
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    features = Feature.objects.all().order_by('name')
    
    return JsonResponse({
        'features': [
            {
                'id': f.id,
                'name': f.name,
                'key': f.key,
                'description': f.description or '',
                'plan_count': f.plan_features.count(),
                'created_at': f.created_at.isoformat(),
            }
            for f in features
        ]
    })