from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime
# import razorpay
import json
import logging
import hashlib
import hmac

from saas.models import Plan, Tenant, PaymentTransaction, Subscription
from saas.forms.tenant_forms import TenantCreationForm


logger = logging.getLogger(__name__)


def tenant_create_view(request):
    """View to collect tenant/company details"""
    plan_id = request.GET.get('plan_id') or request.session.get('selected_plan_id')
    
    if not plan_id:
        messages.error(request, 'Please select a subscription plan first.')
        return redirect('plans:public_list')
    
    try:
        plan = get_object_or_404(Plan, id=plan_id, status=True)
        request.session['selected_plan_id'] = plan_id
    except:
        messages.error(request, 'Invalid subscription plan selected.')
        return redirect('plans:public_list')
    
    if request.method == 'POST':
        form = TenantCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create tenant with inactive status
            tenant = form.save(commit=False)
            tenant.subscription_plan = plan
            tenant.status = 'inactive'  # Will be activated after payment
            tenant.save()
            
            # Store tenant ID in session for payment processing
            request.session['tenant_id'] = tenant.id
            
            # Redirect to payment page
            return redirect('saas:razorpay_payment')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TenantCreationForm()
    
    context = {
        'form': form,
        'plan': plan,
        'page_title': 'Company Setup'
    }
    
    return render(request, 'saas/tenant/create.html', context)


def razorpay_payment_view(request):
    """Initialize Razorpay payment"""
    tenant_id = request.session.get('tenant_id')
    plan_id = request.session.get('selected_plan_id')
    
    if not tenant_id or not plan_id:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('plans:public_list')
    
    try:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        plan = get_object_or_404(Plan, id=plan_id, status=True)
    except:
        messages.error(request, 'Invalid session data.')
        return redirect('plans:public_list')
    
    # Get billing cycle from request (default to monthly)
    billing_cycle = request.GET.get('billing_cycle', 'monthly')
    
    # Calculate amount based on billing cycle
    if billing_cycle == 'yearly':
        amount = int(plan.price_yearly * 100)  # Convert to paise
        display_amount = plan.price_yearly
    else:
        amount = int(plan.price_monthly * 100)  # Convert to paise
        display_amount = plan.price_monthly
        billing_cycle = 'monthly'
    
    # Initialize Razorpay client
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'order_{tenant.id}_{timezone.now().timestamp()}',
            'notes': {
                'tenant_id': tenant.id,
                'plan_id': plan.id,
                'billing_cycle': billing_cycle
            }
        }
        
        order = client.order.create(data=order_data)
        
        # Create payment transaction record
        transaction = PaymentTransaction.objects.create(
            tenant=tenant,
            plan=plan,
            razorpay_order_id=order['id'],
            amount=display_amount,
            billing_cycle=billing_cycle,
            status='created'
        )
        
        context = {
            'tenant': tenant,
            'plan': plan,
            'billing_cycle': billing_cycle,
            'amount': display_amount,
            'order_id': order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'page_title': 'Complete Payment'
        }
        
        return render(request, 'saas/payment/razorpay.html', context)
        
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {str(e)}")
        messages.error(request, 'Payment initialization failed. Please try again.')
        return redirect('tenant_mgmt:create')


@csrf_exempt
@require_http_methods(["POST"])
def razorpay_callback(request):
    """Handle Razorpay payment callback"""
    try:
        # Get payment data from request
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        
        if not all([payment_id, order_id, signature]):
            return JsonResponse({'status': 'error', 'message': 'Missing payment parameters'})
        
        # Get transaction record
        try:
            transaction = PaymentTransaction.objects.get(razorpay_order_id=order_id)
        except PaymentTransaction.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid transaction'})
        
        # Verify signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Generate signature for verification
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != signature:
            transaction.status = 'failed'
            transaction.failure_reason = 'Signature verification failed'
            transaction.save()
            return JsonResponse({'status': 'error', 'message': 'Payment verification failed'})
        
        # Payment successful - activate tenant
        tenant = transaction.tenant
        tenant.status = 'active'
        tenant.subscription_start_date = timezone.now()
        
        # Calculate end date based on billing cycle
        if transaction.billing_cycle == 'yearly':
            tenant.subscription_end_date = tenant.subscription_start_date + timedelta(days=365)
        else:
            tenant.subscription_end_date = tenant.subscription_start_date + timedelta(days=30)
        
        tenant.save()
        
        # Update transaction
        transaction.razorpay_payment_id = payment_id
        transaction.razorpay_signature = signature
        transaction.status = 'paid'
        transaction.save()
        
        # Create subscription record
        Subscription.objects.create(
            tenant=tenant,
            plan=transaction.plan,
            start_date=tenant.subscription_start_date.date(),
            end_date=tenant.subscription_end_date.date(),
            billing_cycle=transaction.billing_cycle,
            amount=transaction.amount,
            status='active'
        )
        
        # Clear session data
        if 'tenant_id' in request.session:
            del request.session['tenant_id']
        if 'selected_plan_id' in request.session:
            del request.session['selected_plan_id']
        
        return JsonResponse({
            'status': 'success',
            'message': 'Payment successful! Your account has been activated.',
            'redirect_url': reverse('saas:dashboard')
        })
        
    except Exception as e:
        logger.error(f"Payment callback error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Payment processing failed'})


def payment_success_view(request):
    """Payment success page"""
    return render(request, 'saas/payment/success.html', {
        'page_title': 'Payment Successful'
    })


def payment_failed_view(request):
    """Payment failed page"""
    return render(request, 'saas/payment/failed.html', {
        'page_title': 'Payment Failed'
    })


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def company_update(request, tenant_id):
    """Update company/tenant details"""
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Company "{tenant.name}" has been updated successfully.')
            return redirect('saas:users')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TenantForm(instance=tenant)
    
    context = {
        'form': form,
        'tenant': tenant,
        'page_title': f'Edit Company - {tenant.name}'
    }
    
    return render(request, 'saas/tenant/edit.html', context)


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def company_delete(request, tenant_id):
    """Delete company/tenant"""
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == 'POST':
        tenant_name = tenant.name
        tenant.delete()
        messages.success(request, f'Company "{tenant_name}" has been deleted successfully.')
        return redirect('saas:users')
    
    # For GET request, show confirmation page
    context = {
        'tenant': tenant,
        'page_title': f'Delete Company - {tenant.name}'
    }
    
    return render(request, 'saas/tenant/delete.html', context)