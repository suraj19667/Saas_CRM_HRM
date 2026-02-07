from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta, date
from decimal import Decimal
from saas.models.tenant import Tenant
from saas.models.subscription import Subscription
from saas.models.plan import Plan
from saas.models.addon import Addon
from saas.models.invoice import Invoice
from saas.models.payment_transaction import PaymentTransaction
from saas.models import CustomUser, Module


@login_required(login_url='auth:login')
def hrm_overview(request):
    """HRM Dashboard Overview - Main dashboard for HRM customers"""
    user = request.user
    
    # Get user's tenant/company
    tenant = None
    if hasattr(user, 'tenant') and user.tenant:
        tenant = user.tenant
    elif hasattr(user, 'company_profile') and user.company_profile:
        tenant = user.company_profile
    
    # If no tenant, redirect to plans selection
    if not tenant:
        return redirect('hrm_plans')
    
    # Get active subscription
    subscription = Subscription.objects.filter(
        tenant=tenant, 
        status='active'
    ).order_by('-created_at').first()
    
    # Get plan details
    plan = subscription.plan if subscription else None
    
    # Calculate REAL usage from database
    # Count employees and admins - use role name filter
    employees_count = CustomUser.objects.filter(
        tenant=tenant, 
        role__name__iexact='employee',
        is_active=True
    ).count()
    
    admins_count = CustomUser.objects.filter(
        tenant=tenant, 
        role__name__iexact='admin',
        is_active=True
    ).count()
    
    # Calculate storage used (simplified - you can implement actual file storage tracking)
    storage_used_gb = 8.5  # This should be calculated from actual file storage
    
    # Count active modules for this tenant
    active_modules = Module.objects.filter(tenant=tenant, is_enabled=True).count()
    total_modules = 8  # Total available modules
    
    # Prepare usage data with real values
    max_users = plan.max_users if plan else 200
    max_storage_gb = (plan.max_storage_mb / 1024) if plan else 10
    
    usage_data = {
        'employees': {
            'current': employees_count,
            'limit': max_users,
            'percentage': int((employees_count / max_users) * 100) if max_users > 0 else 0,
        },
        'admins': {
            'current': admins_count,
            'limit': 5,
            'percentage': int((admins_count / 5) * 100) if admins_count > 0 else 0,
        },
        'storage': {
            'current': storage_used_gb,
            'limit': max_storage_gb,
            'percentage': int((storage_used_gb / max_storage_gb) * 100) if max_storage_gb > 0 else 0,
        },
        'modules': {
            'active': active_modules,
            'available': total_modules,
            'percentage': int((active_modules / total_modules) * 100) if total_modules > 0 else 0,
        }
    }
    
    # Calculate days until renewal
    days_until_renewal = 0
    if subscription and subscription.end_date:
        days_until_renewal = (subscription.end_date - date.today()).days
    
    # Get recent invoices
    recent_invoices = Invoice.objects.filter(
        tenant=tenant
    ).order_by('-created_at')[:3]
    
    context = {
        'tenant': tenant,
        'subscription': subscription,
        'plan': plan,
        'usage_data': usage_data,
        'days_until_renewal': days_until_renewal,
        'recent_invoices': recent_invoices,
        'auto_renew': subscription.status == 'active' if subscription else False,  # Active subscriptions auto-renew
        'purchase_date': subscription.start_date if subscription else None,
        'next_renewal': subscription.end_date if subscription else None,
    }
    
    return render(request, 'hrm/overview.html', context)


@login_required(login_url='auth:login')
def hrm_my_plan(request):
    """HRM My Plan page - Shows current plan details"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    if not tenant:
        return redirect('hrm_plans')
    
    subscription = Subscription.objects.filter(
        tenant=tenant, 
        status='active'
    ).first()
    
    # Get all available plans for upgrade options
    available_plans = Plan.objects.filter(status=True).order_by('price_monthly')
    
    context = {
        'tenant': tenant,
        'subscription': subscription,
        'plan': subscription.plan if subscription else None,
        'available_plans': available_plans,
    }
    
    return render(request, 'hrm/my_plan.html', context)


@login_required(login_url='auth:login')
def hrm_usage(request):
    """HRM Usage & Limits page"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    if not tenant:
        return redirect('hrm_plans')
    
    subscription = Subscription.objects.filter(
        tenant=tenant, 
        status='active'
    ).first()
    
    plan = subscription.plan if subscription else None
    
    # Detailed usage data
    usage_details = {
        'employees': {
            'current': 45,
            'limit': plan.max_users if plan else 50,
            'percentage': 90,
        },
        'admins': {
            'current': 3,
            'limit': 10,
            'percentage': 30,
        },
        'storage': {
            'current': 2.5,
            'limit': (plan.max_storage_mb / 1024) if plan else 5,
            'percentage': 50,
        },
        'projects': {
            'current': 12,
            'limit': plan.max_projects if plan else 20,
            'percentage': 60,
        }
    }
    
    context = {
        'tenant': tenant,
        'subscription': subscription,
        'plan': plan,
        'usage_details': usage_details,
    }
    
    return render(request, 'hrm/usage.html', context)


@login_required(login_url='auth:login')
def hrm_addons(request):
    """HRM Add-ons page"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    if not tenant:
        return redirect('hrm_plans')
    
    # Get available add-ons
    available_addons = Addon.objects.filter(status='active')
    
    # Get tenant's active add-ons (you'll need to track this in your models)
    # For now, we'll use an empty list
    active_addons = []
    
    context = {
        'tenant': tenant,
        'available_addons': available_addons,
        'active_addons': active_addons,
    }
    
    return render(request, 'hrm/addons.html', context)


@login_required(login_url='auth:login')
def hrm_billing(request):
    """HRM Billing & Invoices page"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    if not tenant:
        return redirect('hrm_plans')
    
    # Get all invoices
    invoices = Invoice.objects.filter(
        tenant=tenant
    ).order_by('-created_at')
    
    # Get payment transactions
    transactions = PaymentTransaction.objects.filter(
        tenant=tenant
    ).order_by('-created_at')
    
    # Calculate total spent
    total_spent = transactions.filter(status='paid').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'tenant': tenant,
        'invoices': invoices,
        'transactions': transactions,
        'total_spent': total_spent,
    }
    
    return render(request, 'hrm/billing.html', context)


@login_required(login_url='auth:login')
def hrm_payment_methods(request):
    """HRM Payment Methods page"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    if not tenant:
        return redirect('hrm_plans')
    
    # Get saved payment methods (you'll need to implement this in your models)
    payment_methods = []
    
    context = {
        'tenant': tenant,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'hrm/payment_methods.html', context)


@login_required(login_url='auth:login')
def hrm_account_settings(request):
    """HRM Account Settings page"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    if not tenant:
        return redirect('hrm_plans')
    
    context = {
        'tenant': tenant,
        'user': user,
    }
    
    return render(request, 'hrm/account_settings.html', context)


@login_required(login_url='auth:login')
def hrm_support(request):
    """HRM Support page"""
    user = request.user
    tenant = getattr(user, 'tenant', None) or getattr(user, 'company_profile', None)
    
    context = {
        'tenant': tenant,
    }
    
    return render(request, 'hrm/support.html', context)


@login_required(login_url='auth:login')
def hrm_plans(request):
    """HRM Plans selection page for users without active subscription"""
    user = request.user
    
    # Get all available plans
    plans = Plan.objects.filter(status=True).order_by('price_monthly')
    
    context = {
        'plans': plans,
        'user': user,
    }
    
    return render(request, 'hrm/plans.html', context)


@login_required(login_url='auth:login')
def hrm_home(request):
    """Simple HRM dashboard placeholder - redirects to overview"""
    return redirect('hrm_overview')
