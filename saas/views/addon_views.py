from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from ..models import Addon
from ..forms.addon_forms import AddonForm


def is_admin_user(user):
    """Check if user is admin/superuser"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


@login_required
@user_passes_test(is_admin_user, login_url='dashboard')
def addon_list_view(request):
    """List all add-ons"""
    search_query = request.GET.get('search', '')
    
    addons = Addon.objects.all()
    
    if search_query:
        addons = addons.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    addons = addons.order_by('-created_at')
    
    context = {
        'addons': addons,
        'search_query': search_query,
        'page_title': 'Add-ons Management'
    }
    return render(request, 'addons/addon_list.html', context)


@login_required
@user_passes_test(is_admin_user, login_url='dashboard')
def addon_create_view(request):
    """Create new add-on"""
    if request.method == 'POST':
        form = AddonForm(request.POST)
        if form.is_valid():
            addon = form.save()
            messages.success(request, f'Add-on "{addon.name}" created successfully!')
            return redirect('addon_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddonForm()
    
    context = {
        'form': form,
        'page_title': 'Create Add-on',
        'submit_text': 'Create Add-on'
    }
    return render(request, 'addons/addon_form.html', context)


@login_required
@user_passes_test(is_admin_user, login_url='dashboard')
def addon_edit_view(request, addon_id):
    """Edit existing add-on"""
    addon = get_object_or_404(Addon, id=addon_id)
    
    if request.method == 'POST':
        form = AddonForm(request.POST, instance=addon)
        if form.is_valid():
            addon = form.save()
            messages.success(request, f'Add-on "{addon.name}" updated successfully!')
            return redirect('addon_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddonForm(instance=addon)
    
    context = {
        'form': form,
        'addon': addon,
        'page_title': f'Edit Add-on: {addon.name}',
        'submit_text': 'Update Add-on'
    }
    return render(request, 'addons/addon_form.html', context)


@login_required
@user_passes_test(is_admin_user, login_url='dashboard')
def addon_delete_view(request, addon_id):
    """Delete add-on"""
    addon = get_object_or_404(Addon, id=addon_id)
    
    if request.method == 'POST':
        addon_name = addon.name
        addon.delete()
        messages.success(request, f'Add-on "{addon_name}" deleted successfully!')
        return redirect('addon_list')
    
    context = {
        'addon': addon,
        'page_title': f'Delete Add-on: {addon.name}'
    }
    return render(request, 'addons/addon_delete.html', context)


@login_required
@user_passes_test(is_admin_user, login_url='dashboard')
def addon_toggle_status_view(request, addon_id):
    """Toggle add-on active status"""
    addon = get_object_or_404(Addon, id=addon_id)
    addon.is_active = not addon.is_active
    addon.save()
    
    status_text = 'activated' if addon.is_active else 'deactivated'
    messages.success(request, f'Add-on "{addon.name}" {status_text} successfully!')
    
    return redirect('addon_list')
