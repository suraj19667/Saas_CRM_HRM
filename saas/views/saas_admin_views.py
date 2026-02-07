"""
SaaS Admin Views (Super Admin Dashboard)
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from saas.models import Tenant, Plan, Subscription, CustomUser, PaymentTransaction


def is_super_admin(user):
    """Check if user is super admin"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_super_admin, login_url='/')
def saas_admin_dashboard(request):
    """
    Main SaaS Admin Dashboard
    Shows system-wide statistics and overview
    """
    # Get statistics
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status='active').count()
    total_users = CustomUser.objects.count()
    total_plans = Plan.objects.filter(status=True).count()
    
    # Subscription statistics
    active_subscriptions = Subscription.objects.filter(status='active').count()
    expired_subscriptions = Subscription.objects.filter(status='expired').count()
    
    # Revenue (this month)
    current_month_revenue = PaymentTransaction.objects.filter(
        created_at__month=timezone.now().month,
        status='SUCCESS'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent tenants
    recent_tenants = Tenant.objects.order_by('-created_at')[:10]
    
    # Recent subscriptions
    recent_subscriptions = Subscription.objects.select_related(
        'tenant', 'plan'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'total_users': total_users,
        'total_plans': total_plans,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'current_month_revenue': current_month_revenue,
        'recent_tenants': recent_tenants,
        'recent_subscriptions': recent_subscriptions,
    }
    
    return render(request, 'saas_admin/dashboard.html', context)


@login_required
@user_passes_test(is_super_admin, login_url='/')
def manage_tenants(request):
    """
    Manage all tenants/companies
    """
    tenants = Tenant.objects.annotate(
        user_count=Count('users'),
        subscription_count=Count('subscriptions')
    ).order_by('-created_at')
    
    context = {
        'tenants': tenants,
    }
    
    return render(request, 'saas_admin/tenants.html', context)


@login_required
@user_passes_test(is_super_admin, login_url='/')
def manage_plans(request):
    """
    Manage all subscription plans
    """
    plans = Plan.objects.annotate(
        subscription_count=Count('subscriptions')
    ).order_by('price_monthly')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'saas_admin/plans.html', context)


@login_required
@user_passes_test(is_super_admin, login_url='/')
def manage_subscriptions(request):
    """
    Manage all subscriptions
    """
    subscriptions = Subscription.objects.select_related(
        'tenant', 'plan'
    ).order_by('-created_at')
    
    context = {
        'subscriptions': subscriptions,
    }
    
    return render(request, 'saas_admin/subscriptions.html', context)


@login_required
@user_passes_test(is_super_admin, login_url='/')
def manage_users(request):
    """
    Manage all users across all tenants
    """
    users = CustomUser.objects.select_related(
        'tenant', 'role'
    ).order_by('-date_joined')
    
    context = {
        'users': users,
    }
    
    return render(request, 'saas_admin/users.html', context)


@login_required
@user_passes_test(is_super_admin, login_url='/')
def system_settings(request):
    """
    System-wide settings
    """
    context = {}
    
    return render(request, 'saas_admin/settings.html', context)
