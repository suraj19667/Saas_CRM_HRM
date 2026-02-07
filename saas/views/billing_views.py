"""
Billing and Pricing Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from saas.models import Plan, Tenant, Subscription, PaymentTransaction


def pricing_page(request):
    """
    Public pricing page showing all available plans
    """
    plans = Plan.objects.filter(is_active=True).order_by('price_monthly')
    
    context = {
        'plans': plans,
        'user': request.user if request.user.is_authenticated else None,
    }
    
    return render(request, 'billing/pricing.html', context)


@login_required
def select_plan(request, plan_id):
    """
    User selects a plan and proceeds to checkout
    """
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    
    # Check if user has a tenant
    tenant = getattr(request.user, 'tenant', None)
    
    if not tenant:
        messages.error(request, 'You need to create a company profile first.')
        return redirect('/')
    
    # Store selected plan in session
    request.session['selected_plan_id'] = plan.id
    
    return redirect('billing:checkout', plan_id=plan.id)


@login_required
def checkout(request, plan_id):
    """
    Checkout page for plan subscription
    """
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    tenant = getattr(request.user, 'tenant', None)
    
    if not tenant:
        messages.error(request, 'You need to create a company profile first.')
        return redirect('/')
    
    if request.method == 'POST':
        billing_cycle = request.POST.get('billing_cycle', 'monthly')
        
        # Calculate amount based on billing cycle
        if billing_cycle == 'yearly':
            amount = plan.price_yearly if plan.price_yearly else plan.price_monthly * 12
            duration_days = 365
        else:
            amount = plan.price_monthly
            duration_days = 30
        
        # Create subscription
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=duration_days)
        
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            billing_cycle=billing_cycle,
            amount=amount,
            status='active'  # In production, this would be 'pending' until payment
        )
        
        # Create payment transaction
        PaymentTransaction.objects.create(
            tenant=tenant,
            plan=plan,
            subscription=subscription,
            amount=amount,
            currency='USD',
            status='SUCCESS',  # In production, integrate with payment gateway
            billing_cycle=billing_cycle
        )
        
        messages.success(request, f'Successfully subscribed to {plan.name} plan!')
        
        # Redirect to login instead of directly to HRM
        return redirect('auth:login')
    
    context = {
        'plan': plan,
        'tenant': tenant,
    }
    
    return render(request, 'billing/checkout.html', context)


@login_required
def payment_success(request):
    """
    Payment success page
    """
    messages.success(request, 'Payment successful! Your subscription is now active.')
    return redirect('auth:login')


@login_required
def payment_failed(request):
    """
    Payment failed page
    """
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('billing:pricing')
