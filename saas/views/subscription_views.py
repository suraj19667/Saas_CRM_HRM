from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from saas.models.plan import Plan
from saas.models.subscription import Subscription
from saas.models.tenant import Tenant
from saas.forms.plan_forms import PlanForm
from saas.forms.tenant_forms import TenantCreationForm


@login_required(login_url='auth:login')
def list_plans(request):
    """List available plans for tenants"""
    plans = Plan.objects.filter(status=True).prefetch_related('plan_features__feature').order_by('price_monthly')
    # Get current active subscription for the user's tenant
    current_subscription = None
    try:
        tenant = request.user.tenant
        if tenant:
            current_subscription = Subscription.objects.filter(
                tenant=tenant,
                status='active'
            ).first()
    except AttributeError:
        pass
    
    # Check if user is super admin
    is_super_admin = request.user.is_superuser or request.user.is_staff
    
    context = {
        'plans': plans,
        'current_subscription': current_subscription,
        'page_title': 'Available Plans',
        'is_super_admin': is_super_admin,
    }
    return render(request, 'subscription/list_plans.html', context)


@login_required(login_url='auth:login')
def subscribe_plan(request, plan_id):
    """Subscribe to a plan - Step 1: Show tenant registration form"""
    plan = get_object_or_404(Plan, id=plan_id, status=True)
    
    # Check if user already has a tenant
    has_tenant = False
    try:
        tenant = request.user.tenant
        if tenant:
            has_tenant = True
    except AttributeError:
        pass
    
    if has_tenant:
        # User already has tenant, redirect to payment
        return redirect('subscription:process_payment', plan_id=plan_id)
    
    # Show tenant registration form
    if request.method == 'POST':
        form = TenantCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create tenant
            tenant = form.save(commit=False)
            tenant.status = 'inactive'  # Will be activated after payment
            tenant.save()
            
            # Associate user with tenant
            request.user.tenant = tenant
            request.user.save()
            
            messages.success(request, 'Company details saved! Proceeding to payment...')
            return redirect('subscription:process_payment', plan_id=plan_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TenantCreationForm()
    
    context = {
        'form': form,
        'plan': plan,
        'page_title': f'Register Your Company - Subscribe to {plan.name}',
    }
    return render(request, 'subscription/tenant_registration_form.html', context)


@login_required(login_url='auth:login')
def cancel_subscription(request, subscription_id):
    """Cancel a subscription"""
    try:
        tenant = request.user.tenant
    except AttributeError:
        tenant = None
    
    if not tenant:
        messages.error(request, 'You must be associated with a tenant to manage subscriptions.')
        return redirect('subscription:list_plans')
    
    subscription = get_object_or_404(Subscription, id=subscription_id, tenant=tenant)
    
    if subscription.status != 'active':
        messages.error(request, 'Subscription is not active.')
        return redirect('subscription:list_plans')
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.save()
        messages.success(request, 'Subscription cancelled successfully.')
        return redirect('subscription:list_plans')
    
    context = {
        'subscription': subscription,
        'page_title': 'Cancel Subscription',
    }
    return render(request, 'subscription/cancel_subscription.html', context)


@login_required(login_url='auth:login')
def process_payment(request, plan_id):
    """Process payment for subscription - Step 2: Payment Gateway"""
    plan = get_object_or_404(Plan, id=plan_id, status=True)
    
    # Get user's tenant
    try:
        tenant = request.user.tenant
        if not tenant:
            messages.error(request, 'Please complete company registration first.')
            return redirect('subscription:subscribe_plan', plan_id=plan_id)
    except AttributeError:
        messages.error(request, 'Please complete company registration first.')
        return redirect('subscription:subscribe_plan', plan_id=plan_id)
    
    # Check if tenant already has an active subscription
    active_subscription = Subscription.objects.filter(
        tenant=tenant,
        status='active'
    ).first()
    
    if active_subscription:
        messages.error(request, 'You already have an active subscription.')
        return redirect('subscription:list_plans')
    
    if request.method == 'POST':
        billing_cycle = request.POST.get('billing_cycle', 'monthly')
        payment_method = request.POST.get('payment_method', 'razorpay')
        
        if billing_cycle not in ['monthly', 'yearly']:
            messages.error(request, 'Invalid billing cycle.')
            return redirect('subscription:process_payment', plan_id=plan_id)
        
        # Calculate amount
        amount = plan.price_monthly if billing_cycle == 'monthly' else plan.price_yearly
        
        # Calculate subscription dates
        start_date = timezone.now()
        if billing_cycle == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:
            end_date = start_date + timedelta(days=365)
        
        # Create subscription
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            start_date=start_date.date(),
            billing_cycle=billing_cycle,
            amount=amount,
            status='active'
        )
        
        # Update tenant subscription details
        tenant.subscription_plan = plan
        tenant.subscription_start_date = start_date
        tenant.subscription_end_date = end_date
        tenant.status = 'active'
        tenant.save()
        
        messages.success(request, f'Payment successful! Welcome to {plan.name} plan!')
        return redirect('subscription:payment_success', subscription_id=subscription.id)
    
    context = {
        'plan': plan,
        'tenant': tenant,
        'page_title': f'Payment - {plan.name} Plan',
    }
    return render(request, 'subscription/payment_gateway.html', context)


@login_required(login_url='auth:login')
def payment_success(request, subscription_id):
    """Payment success - Step 3: Show demo dashboard"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    # Verify user has access to this subscription
    try:
        tenant = request.user.tenant
        if not tenant or subscription.tenant != tenant:
            messages.error(request, 'Access denied.')
            return redirect('subscription:list_plans')
    except AttributeError:
        messages.error(request, 'Access denied.')
        return redirect('subscription:list_plans')
    
    context = {
        'subscription': subscription,
        'plan': subscription.plan,
        'tenant': tenant,
        'page_title': 'Welcome to Your Dashboard!',
    }
    return render(request, 'subscription/payment_success_dashboard.html', context)
