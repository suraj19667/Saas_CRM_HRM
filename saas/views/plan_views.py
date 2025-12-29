from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from saas.models.plan import Plan, OneTimePlan, CustomEnterprisePlan
from saas.models.feature import Feature
from saas.models.planfeature import PlanFeature
from ..forms.plan_forms import PlanForm
from ..forms.planfeature_forms import PlanFeatureForm, PlanFeatureInlineForm


def public_plan_list(request):
    """
    Public view to display available subscription plans for customers.
    """
    plans = Plan.objects.filter(status=True).order_by('price_monthly')
    context = {
        'plans': plans,
        'page_title': 'Choose Your Plan',
    }
    return render(request, 'saas/plans/public_list.html', context)


def is_super_admin(user):
    """Check if user is a super admin."""
    return user.is_superuser or user.is_staff


@login_required(login_url='auth:login')
def plan_list(request):
    """
    Display list of all plans.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to access plans.')
        return redirect('dashboard')
    
    plans = Plan.objects.all().order_by('price_monthly')
    context = {
        'plans': plans,
        'page_title': 'Subscription Plans',
    }
    return render(request, 'plans/plan_list.html', context)


@login_required(login_url='auth:login')
def one_time_plans(request):
    """
    Display list of one-time plans.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to access plans.')
        return redirect('dashboard')
    
    plans = OneTimePlan.objects.all().order_by('-created_date')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'plans': page_obj,
        'page_title': 'One Time Plans',
        'plan_type': 'one_time',
    }
    return render(request, 'plans/one_time_plan.html', context)


@login_required(login_url='auth:login')
def subscription_plans(request):
    """
    Display list of subscription plans.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to access plans.')
        return redirect('dashboard')
    
    plans = Plan.objects.filter(plan_type='subscription').order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'plans': page_obj,
        'page_title': 'Subscription Plans',
        'plan_type': 'subscription',
    }
    return render(request, 'plans/subscription_plan.html', context)


@login_required(login_url='auth:login')
def custom_plans(request):
    """
    Display list of custom plans.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to access plans.')
        return redirect('dashboard')
    
    plans = CustomEnterprisePlan.objects.all().order_by('-created_date')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'plans': page_obj,
        'page_title': 'Custom Plans',
        'plan_type': 'custom',
    }
    return render(request, 'plans/custom_plan.html', context)


@login_required(login_url='auth:login')
def plan_create(request):
    """
    Create a new plan with module access.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to create plans.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            
            # Handle module access
            module_features = _process_module_access(request.POST)
            _assign_features_to_plan(plan, module_features)
            
            # Store support level in plan metadata or custom field
            support_level = request.POST.get('support_level', 'basic')
            # If you have a support_level field in Plan model, uncomment:
            # plan.support_level = support_level
            # plan.save()
            
            messages.success(request, f'✅ Plan "{plan.name}" created successfully!')
            
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Plan {plan.name} created!', 'plan_id': plan.id})
            
            return redirect('plans:plan_list')
        else:
            # Surface form validation errors to the user via messages
            for field, errs in form.errors.items():
                # non_field_errors come as '__all__' in some cases
                if field == '__all__':
                    for e in errs:
                        messages.error(request, e)
                else:
                    for e in errs:
                        messages.error(request, f"{field}: {e}")
    else:
        form = PlanForm()
    
    context = {
        'form': form,
        'page_title': 'Create New Plan',
        'active_modules': [],
        'storage_gb_display': '',
        'plan': None,
    }
    return render(request, 'plans/plan_form.html', context)


@login_required(login_url='auth:login')
def plan_edit(request, plan_id):
    """
    Edit an existing plan with module access.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to edit plans.')
        return redirect('dashboard')
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            
            # Handle module access updates
            module_features = _process_module_access(request.POST)
            _assign_features_to_plan(plan, module_features, update=True)
            
            # Update support level
            support_level = request.POST.get('support_level', 'basic')
            # If you have a support_level field in Plan model, uncomment:
            # plan.support_level = support_level
            # plan.save()
            
            messages.success(request, f'✅ Plan "{plan.name}" updated successfully!')
            
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Plan {plan.name} updated!', 'plan_id': plan.id})
            
            return redirect('plans:plan_list')
        else:
            # Surface form validation errors to the user via messages
            for field, errs in form.errors.items():
                if field == '__all__':
                    for e in errs:
                        messages.error(request, e)
                else:
                    for e in errs:
                        messages.error(request, f"{field}: {e}")
    else:
        form = PlanForm(instance=plan)
    
    # Get current plan modules for pre-filling checkboxes
    plan_features = PlanFeature.objects.filter(plan=plan).select_related('feature')
    active_modules = [pf.feature.key for pf in plan_features]
    
    # Convert storage MB to GB for display
    storage_gb_display = plan.max_storage_mb / 1024 if plan.max_storage_mb else 0
    
    context = {
        'form': form,
        'plan': plan,
        'active_modules': active_modules,
        'storage_gb_display': storage_gb_display,
        'page_title': f'Edit Plan - {plan.name}',
    }
    return render(request, 'plans/plan_form.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def plan_delete(request, plan_id):
    """
    Delete a plan.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to delete plans.')
        return redirect('dashboard')
    
    plan = get_object_or_404(Plan, id=plan_id)
    plan_name = plan.name
    plan.delete()
    
    messages.success(request, f'Plan "{plan_name}" deleted successfully!')
    return redirect('plans:plan_list')


@login_required(login_url='auth:login')
def plan_features_manage(request, plan_id):
    """
    Manage features for a specific plan.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to manage plan features.')
        return redirect('dashboard')
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # Get all features assigned to this plan
    plan_features = PlanFeature.objects.filter(plan=plan).select_related('feature')
    
    # Get all available features not yet assigned
    assigned_feature_ids = plan_features.values_list('feature_id', flat=True)
    available_features = Feature.objects.exclude(id__in=assigned_feature_ids)
    
    context = {
        'plan': plan,
        'plan_features': plan_features,
        'available_features': available_features,
        'page_title': f'Manage Features - {plan.name}',
    }
    return render(request, 'plans/plan_features_manage.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def plan_feature_add(request, plan_id):
    """
    Add a feature to a plan.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to add plan features.')
        return redirect('dashboard')
    
    plan = get_object_or_404(Plan, id=plan_id)
    feature_id = request.POST.get('feature')
    feature_limit = request.POST.get('feature_limit')
    
    if not feature_id:
        messages.error(request, 'Please select a feature.')
        return redirect('plans:plan_features_manage', plan_id=plan_id)
    
    feature = get_object_or_404(Feature, id=feature_id)
    
    # Check if feature already exists for this plan
    if PlanFeature.objects.filter(plan=plan, feature=feature).exists():
        messages.warning(request, f'Feature "{feature.name}" is already added to this plan.')
        return redirect('plans:plan_features_manage', plan_id=plan_id)
    
    # Convert empty string to None for unlimited
    if feature_limit == '' or feature_limit is None:
        feature_limit = None
    else:
        try:
            feature_limit = int(feature_limit)
        except ValueError:
            feature_limit = None
    
    # Create the plan feature
    PlanFeature.objects.create(
        plan=plan,
        feature=feature,
        feature_limit=feature_limit
    )
    
    limit_text = f"with limit {feature_limit}" if feature_limit else "with unlimited access"
    messages.success(request, f'Feature "{feature.name}" added to plan "{plan.name}" {limit_text}!')
    return redirect('plans:plan_features_manage', plan_id=plan_id)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def plan_feature_update(request, plan_id, plan_feature_id):
    """
    Update a plan feature limit.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to update plan features.')
        return redirect('dashboard')
    
    plan = get_object_or_404(Plan, id=plan_id)
    plan_feature = get_object_or_404(PlanFeature, id=plan_feature_id, plan=plan)
    feature_limit = request.POST.get('feature_limit')
    
    # Convert empty string to None for unlimited
    if feature_limit == '' or feature_limit is None:
        plan_feature.feature_limit = None
    else:
        try:
            plan_feature.feature_limit = int(feature_limit)
        except ValueError:
            plan_feature.feature_limit = None
    
    plan_feature.save()
    
    limit_text = f"to {plan_feature.feature_limit}" if plan_feature.feature_limit else "to unlimited"
    messages.success(request, f'Feature "{plan_feature.feature.name}" limit updated {limit_text}!')
    return redirect('plans:plan_features_manage', plan_id=plan_id)


@login_required(login_url='auth:login')
@require_http_methods(['POST'])
def plan_feature_delete(request, plan_id, plan_feature_id):
    """
    Remove a feature from a plan.
    """
    if not is_super_admin(request.user):
        messages.error(request, 'You do not have permission to delete plan features.')
        return redirect('dashboard')
    
    plan = get_object_or_404(Plan, id=plan_id)
    plan_feature = get_object_or_404(PlanFeature, id=plan_feature_id, plan=plan)
    feature_name = plan_feature.feature.name
    plan_feature.delete()
    
    messages.success(request, f'Feature "{feature_name}" removed from plan "{plan.name}"!')
    return redirect('plans:plan_features_manage', plan_id=plan_id)


# Helper functions
def _process_module_access(post_data):
    """
    Process module access checkboxes from POST data.
    Returns a dict mapping feature keys to whether they're enabled.
    """
    module_mapping = {
        'module_employee': 'employee_management',
        'module_attendance': 'attendance_management',
        'module_leave': 'leave_management',
        'module_payroll': 'payroll_management',
        'module_expense': 'expense_management',
        'module_broadcast': 'broadcast_messages',
        'module_analytics': 'analytics_module',
    }
    
    enabled_modules = {}
    for post_key, feature_key in module_mapping.items():
        # Checkbox is present in POST if checked, absent if unchecked
        enabled_modules[feature_key] = post_key in post_data
    
    return enabled_modules


def _assign_features_to_plan(plan, module_features, update=False):
    """
    Assign features to a plan based on module selection.
    If update=True, removes unchecked features.
    """
    # If updating, remove all existing plan features first
    if update:
        PlanFeature.objects.filter(plan=plan).delete()
    
    # Add enabled features
    for feature_key, is_enabled in module_features.items():
        if is_enabled:
            try:
                feature = Feature.objects.get(key=feature_key)
                PlanFeature.objects.get_or_create(
                    plan=plan,
                    feature=feature,
                    defaults={'feature_limit': None}  # Unlimited by default
                )
            except Feature.DoesNotExist:
                # Feature doesn't exist in database, skip it
                continue