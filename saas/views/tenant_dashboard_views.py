from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from ..models import Tenant, CompanySubscription


@login_required
def tenant_dashboard_view(request):
    """Tenant-specific dashboard"""
    # Tenant is already validated in middleware or use user's tenant
    tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)

    if not tenant:
        messages.error(request, 'No tenant found for this session.')
        return redirect('company:login')

    # Filter data by tenant
    from ..models import CustomUser, Role
    users = CustomUser.objects.filter(tenant=tenant).select_related('role')
    roles = Role.objects.filter(tenant=tenant).prefetch_related('users')

    context = {
        'users': users,
        'roles': roles,
        'tenant': tenant,
    }

    response = render(request, 'dashboard.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def tenant_feature_check(request, tenant_slug, feature_name):
    """Check if tenant has access to a feature"""
    try:
        tenant = request.user.tenant
        subscription = CompanySubscription.objects.get(
            tenant=tenant,
            status='active'
        )

        if not subscription.is_active():
            return {'access': False, 'reason': 'subscription_expired'}

        # Check feature in plan
        plan_features = subscription.plan.features
        if isinstance(plan_features, str):
            import json
            plan_features = json.loads(plan_features)

        if feature_name in plan_features and plan_features[feature_name]:
            return {'access': True}
        else:
            return {'access': False, 'reason': 'feature_not_allowed'}

    except (Tenant.DoesNotExist, CompanySubscription.DoesNotExist):
        return {'access': False, 'reason': 'no_subscription'}


def tenant_dashboard(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug)

    # Check subscription validity
    if not tenant.is_subscription_active:
        return redirect("subscription_plans")

    # Dummy data for user count and storage usage
    context = {
        "company_name": tenant.name,
        "active_plan": tenant.subscription_plan,
        "subscription_start_date": tenant.subscription_start_date,
        "subscription_end_date": tenant.subscription_end_date,
        "user_count": 10,  # Replace with actual logic
        "storage_usage": "2GB / 10GB"  # Replace with actual logic
    }
    return render(request, "dashboard/tenant_dashboard.html", context)