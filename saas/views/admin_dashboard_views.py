"""
Admin Dashboard Views for SaaS Admin Panel
All views require superuser or staff access
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_http_methods

from ..models import (
    Tenant, Subscription, Invoice, CustomUser, Plan,
    OneTimePlan, SubscriptionBillingPlan, CustomEnterprisePlan,
    Discount, CompanySubscription, PaymentTransaction
)


def is_super_admin(user):
    """Check if user is super admin"""
    return user.is_superuser or user.is_staff


@login_required(login_url='auth:login')
def admin_dashboard(request):
    """Main admin dashboard with metrics and charts"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Calculate metrics
    total_companies = Tenant.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    total_invoices = Invoice.objects.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Monthly revenue (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_revenue = Invoice.objects.filter(
        status='paid',
        invoice_date__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Active trials
    active_trials = Tenant.objects.filter(status='inactive').count()
    
    # Suspended accounts
    suspended_accounts = Tenant.objects.filter(status='inactive').count()
    
    # Trial conversion rate (simplified)
    total_trials = Tenant.objects.count()
    converted = Subscription.objects.filter(status='active').count()
    trial_conversion_rate = (converted / total_trials * 100) if total_trials > 0 else 0
    
    # Total admin users
    total_admin_users = CustomUser.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).count()
    
    # Churn risk (subscriptions expiring in next 30 days)
    thirty_days_from_now = timezone.now() + timedelta(days=30)
    churn_risk = Subscription.objects.filter(
        status='active',
        end_date__lte=thirty_days_from_now,
        end_date__gte=timezone.now().date()
    ).count()
    
    # Recent activity (last 10 subscriptions)
    recent_activity = Subscription.objects.select_related(
        'tenant', 'plan'
    ).order_by('-created_at')[:10]
    
    # Upcoming renewals (next 7 days)
    seven_days_from_now = timezone.now() + timedelta(days=7)
    upcoming_renewals = Subscription.objects.filter(
        status='active',
        end_date__lte=seven_days_from_now,
        end_date__gte=timezone.now().date()
    ).select_related('tenant', 'plan').order_by('end_date')[:10]
    
    # Revenue overview (last 12 months)
    revenue_data = []
    for i in range(11, -1, -1):
        month_start = timezone.now() - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        month_revenue = Invoice.objects.filter(
            status='paid',
            invoice_date__gte=month_start.date(),
            invoice_date__lt=month_end.date()
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_data.append({
            'month': month_start.strftime('%b'),
            'revenue': float(month_revenue)
        })
    
    import json
    revenue_data_json = json.dumps(revenue_data)
    
    # Plan distribution
    plan_distribution = Subscription.objects.filter(
        status='active'
    ).values('plan__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_companies': total_companies,
        'active_subscriptions': active_subscriptions,
        'monthly_revenue': monthly_revenue,
        'active_trials': active_trials,
        'suspended_accounts': suspended_accounts,
        'trial_conversion_rate': round(trial_conversion_rate, 1),
        'total_admin_users': total_admin_users,
        'churn_risk': churn_risk,
        'recent_activity': recent_activity,
        'upcoming_renewals': upcoming_renewals,
        'revenue_data': revenue_data_json,
        'plan_distribution': plan_distribution,
    }
    
    return render(request, 'admin/admin_dashboard.html', context)


@login_required(login_url='auth:login')
def subscription_list(request):
    """Subscription list page showing all company subscriptions"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    plan_filter = request.GET.get('plan', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Base queryset
    subscriptions = Subscription.objects.select_related(
        'tenant', 'plan'
    ).order_by('-created_at')
    
    # Apply filters
    if search_query:
        subscriptions = subscriptions.filter(
            Q(tenant__name__icontains=search_query) |
            Q(tenant__contact_email__icontains=search_query)
        )
    
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    
    if plan_filter:
        subscriptions = subscriptions.filter(plan_id=plan_filter)
    
    if date_from:
        subscriptions = subscriptions.filter(created_at__gte=date_from)
    
    if date_to:
        subscriptions = subscriptions.filter(created_at__lte=date_to)
    
    # Calculate metrics
    total_companies = Tenant.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    monthly_revenue = Invoice.objects.filter(
        status='paid',
        invoice_date__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    active_trials = Tenant.objects.filter(status='inactive').count()
    
    # Pagination
    paginator = Paginator(subscriptions, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get available plans for filter
    plans = Plan.objects.all().order_by('name')
    
    context = {
        'subscriptions': page_obj,
        'pagination': page_obj,
        'total_companies': total_companies,
        'active_subscriptions': active_subscriptions,
        'monthly_revenue': monthly_revenue,
        'active_trials': active_trials,
        'plans': plans,
        'search_query': search_query,
        'status_filter': status_filter,
        'plan_filter': plan_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'admin/subscription_list.html', context)


@login_required(login_url='auth:login')
def subscription_plans_admin(request):
    """Admin view for subscription plans management"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    plan_filter = request.GET.get('plan', '').strip()
    
    # Base queryset - using SubscriptionBillingPlan model
    subscriptions = SubscriptionBillingPlan.objects.select_related().order_by('-created_date')
    
    # Apply filters
    if search_query:
        subscriptions = subscriptions.filter(
            Q(company_name__icontains=search_query) |
            Q(company_email__icontains=search_query)
        )
    
    if status_filter:
        subscriptions = subscriptions.filter(subscription_status=status_filter)
    
    # Calculate metrics
    active_subscriptions_count = SubscriptionBillingPlan.objects.filter(
        subscription_status='active'
    ).count()
    
    # Monthly recurring revenue
    monthly_recurring = SubscriptionBillingPlan.objects.filter(
        subscription_status='active',
        billing_type='monthly'
    ).aggregate(total=Sum('monthly_price'))['total'] or 0
    
    # Expiring this month
    month_end = timezone.now() + timedelta(days=30)
    expiring_this_month = SubscriptionBillingPlan.objects.filter(
        subscription_status='active'
    ).count()  # Simplified - would need end_date field
    
    # Cancelled in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    cancelled_recent = SubscriptionBillingPlan.objects.filter(
        subscription_status='cancelled',
        updated_at__gte=thirty_days_ago
    ).count()
    
    # Pagination
    paginator = Paginator(subscriptions, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'subscriptions': page_obj,
        'active_subscriptions': active_subscriptions_count,
        'monthly_recurring': monthly_recurring,
        'expiring_this_month': expiring_this_month,
        'cancelled_recent': cancelled_recent,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/subscription_plans.html', context)


@login_required(login_url='auth:login')
def one_time_plans_admin(request):
    """Admin view for one-time plans"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    # Base queryset
    plans = OneTimePlan.objects.all().order_by('-created_date')
    
    # Apply filters
    if search_query:
        plans = plans.filter(license_name__icontains=search_query)
    
    if status_filter:
        plans = plans.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'plans': page_obj,
        'pagination': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/one_time_plans.html', context)


@login_required(login_url='auth:login')
def custom_plans_admin(request):
    """Admin view for custom enterprise plans"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    # Base queryset
    plans = CustomEnterprisePlan.objects.all().order_by('-created_date')
    
    # Apply filters
    if search_query:
        plans = plans.filter(
            Q(company_name__icontains=search_query) |
            Q(plan_name__icontains=search_query)
        )
    
    if status_filter:
        plans = plans.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'plans': page_obj,
        'pagination': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/custom_plans.html', context)


@login_required(login_url='auth:login')
def discount_list(request):
    """Discount list page"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    scope_filter = request.GET.get('scope', '').strip()
    type_filter = request.GET.get('type', '').strip()
    
    # Base queryset
    discounts = Discount.objects.select_related('created_by').order_by('-created_at')
    
    # Apply filters
    if search_query:
        discounts = discounts.filter(discount_name__icontains=search_query)
    
    if status_filter:
        discounts = discounts.filter(status=status_filter)
    
    if scope_filter:
        discounts = discounts.filter(scope=scope_filter)
    
    if type_filter:
        discounts = discounts.filter(discount_type=type_filter)
    
    # Calculate metrics
    active_discounts = Discount.objects.filter(status='active').count()
    
    # Total usage in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    total_usage = Discount.objects.filter(
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('current_usage'))['total'] or 0
    
    # Total savings (simplified calculation)
    total_savings = 0  # Would need transaction records to calculate
    
    # Expiring this month
    month_end = timezone.now() + timedelta(days=30)
    expiring_this_month = Discount.objects.filter(
        status='active',
        end_date__lte=month_end.date(),
        end_date__gte=timezone.now().date()
    ).count()
    
    # Pagination
    paginator = Paginator(discounts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'discounts': page_obj,
        'pagination': page_obj,
        'active_discounts': active_discounts,
        'total_usage': total_usage,
        'total_savings': total_savings,
        'expiring_this_month': expiring_this_month,
        'search_query': search_query,
        'status_filter': status_filter,
        'scope_filter': scope_filter,
        'type_filter': type_filter,
    }
    
    return render(request, 'admin/discount_list.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def discount_create(request):
    """Create new discount"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        from ..forms.discount_forms import DiscountForm
        form = DiscountForm(request.POST)
        if form.is_valid():
            discount = form.save(commit=False)
            discount.created_by = request.user
            discount.save()
            messages.success(request, f'Discount "{discount.discount_name}" created successfully!')
            return redirect('saas_admin:discount_list')
    else:
        from ..forms.discount_forms import DiscountForm
        form = DiscountForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'admin/discount_create.html', context)


@login_required(login_url='auth:login')
def invoice_billing(request):
    """Invoice & Billing page"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    plan_filter = request.GET.get('plan', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Base queryset
    invoices = Invoice.objects.select_related(
        'tenant', 'subscription'
    ).order_by('-created_at')
    
    # Apply filters
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(tenant__name__icontains=search_query)
        )
    
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)
    
    # Calculate metrics
    total_revenue = Invoice.objects.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    pending_amount = Invoice.objects.filter(status='unpaid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    overdue_amount = Invoice.objects.filter(status='overdue').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_invoices = invoices.count()
    
    # Pagination
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'invoices': page_obj,
        'pagination': page_obj,
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'overdue_amount': overdue_amount,
        'total_invoices': total_invoices,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'admin/invoice_billing.html', context)


@login_required(login_url='auth:login')
def admin_users(request):
    """Admin users management page"""
    if not is_super_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    # Base queryset - only staff/superuser
    users = CustomUser.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).select_related('role').order_by('-date_joined')
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role_id=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Calculate role counts
    from ..models import Role
    role_counts = {}
    for role in Role.objects.all():
        count = users.filter(role=role).count()
        total = Role.objects.filter(id=role.id).count()  # Total users with this role
        role_counts[role.name] = {'current': count, 'total': total}
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get available roles for filter
    roles = Role.objects.all().order_by('name')
    
    context = {
        'users': page_obj,
        'pagination': page_obj,
        'role_counts': role_counts,
        'roles': roles,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/admin_users.html', context)

