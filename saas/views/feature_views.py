from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from saas.models.feature import Feature
from ..forms.feature_forms import FeatureForm


def is_super_admin(user):
    """Check if user is a super admin."""
    return user.is_superuser or user.is_staff


@login_required(login_url='auth:login')
def feature_list(request):
    """
    Display list of all features.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to access features.')
        return redirect('dashboard')

    features = Feature.objects.all().order_by('name')
    context = {
        'features': features,
        'page_title': 'Manage Features',
    }
    return render(request, 'features/feature_list.html', context)


@login_required(login_url='auth:login')
def feature_create(request):
    """
    Create a new feature.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to create features.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = FeatureForm(request.POST)
        if form.is_valid():
            feature = form.save()
            messages.success(request, f'Feature "{feature.name}" created successfully!')
            return redirect('features:feature_list')
    else:
        form = FeatureForm()

    context = {
        'form': form,
        'page_title': 'Create Feature',
    }
    return render(request, 'features/feature_form.html', context)


@login_required(login_url='auth:login')
def feature_edit(request, feature_id):
    """
    Edit an existing feature.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to edit features.')
        return redirect('dashboard')

    feature = get_object_or_404(Feature, id=feature_id)

    if request.method == 'POST':
        form = FeatureForm(request.POST, instance=feature)
        if form.is_valid():
            feature = form.save()
            messages.success(request, f'Feature "{feature.name}" updated successfully!')
            return redirect('features:feature_list')
    else:
        form = FeatureForm(instance=feature)

    context = {
        'form': form,
        'feature': feature,
        'page_title': 'Edit Feature',
    }
    return render(request, 'features/feature_form.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def feature_delete(request, feature_id):
    """
    Delete a feature.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to delete features.')
        return redirect('dashboard')

    feature = get_object_or_404(Feature, id=feature_id)
    feature_name = feature.name
    
    # Check if feature is used in any plans
    if feature.plan_features.exists():
        plan_count = feature.plan_features.count()
        messages.warning(
            request, 
            f'Cannot delete feature "{feature_name}" as it is used in {plan_count} plan(s). '
            'Please remove it from all plans first.'
        )
    else:
        feature.delete()
        messages.success(request, f'Feature "{feature_name}" deleted successfully!')
    
    return redirect('features:feature_list')
