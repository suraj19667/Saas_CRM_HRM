from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import requests
import json
import uuid
from ..models import CustomUser, Tenant, CompanySubscription, Plan, PaymentTransaction
from ..forms import CompanyRegistrationForm, CompanyLoginForm
from django.db import IntegrityError


def company_register_view(request):
    """Company registration view"""
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            # Create tenant (domain will be auto-generated via signal)
            tenant = Tenant.objects.create(
                name=form.cleaned_data['company_name'],
                contact_email=form.cleaned_data['email'],
                status='inactive',  # Tenant starts inactive until subscription
                allow_email_notifications=True,  # Set default notification preferences
                allow_sms_notifications=False
            )

            # Create user (guard against race/DB unique failures)
            try:
                user = CustomUser.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    tenant=tenant,
                    is_verified=True
                )
            except IntegrityError:
                # Clean up created tenant to avoid orphaned records and inform the user
                tenant.delete()
                messages.error(request, 'A user with this email already exists. Please use a different email or login.')
                return redirect('company:register')

            messages.success(request, 'Company registered successfully! Please login to continue.')
            return redirect('company:login')  # Redirect to login, no auto-login
    else:
        form = CompanyRegistrationForm()

    return render(request, 'company/register.html', {'form': form})


def company_login_view(request, tenant_domain=None):
    """Company login view"""
    if request.method == 'POST':
        form = CompanyLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password, backend='django.contrib.auth.backends.ModelBackend')
            if user:
                if not user.is_verified:
                    messages.error(request, 'Please verify your email before logging in.')
                    return redirect('login')
                
                # Check if user belongs to the tenant
                # For company login, allow login if user has a tenant
                if user.tenant:
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'Logged in successfully!')
                    # Redirect based on tenant status
                    if user.tenant.status == 'inactive':
                        return redirect('company:subscription_plans')
                    else:
                        return redirect(reverse('tenant:tenant_dashboard', kwargs={'tenant_slug': user.tenant.slug}))
                else:
                    messages.error(request, 'User account is not associated with any company.')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = CompanyLoginForm()

    return render(request, 'company/login.html', {'form': form})


@login_required
def subscription_plans_view(request):
    """Show subscription plans for company"""
    plans = Plan.objects.filter(status=True).prefetch_related('plan_features__feature')  # Only active plans with features
    return render(request, 'company/subscription_plans.html', {'plans': plans})


@login_required
def update_tenant_info(request):
    """Update tenant information before payment"""
    if request.method == 'POST':
        try:
            tenant = request.user.tenant
            
            # Debug print
            print(f"Updating tenant: {tenant.name if tenant else 'None'}")
            print(f"Contact Phone: {request.POST.get('contact_phone', '')}")
            print(f"Address: {request.POST.get('address', '')}")
            
            if not tenant:
                return JsonResponse({'success': False, 'error': 'No tenant found for user'})
            
            tenant.contact_phone = request.POST.get('contact_phone', '')
            tenant.address = request.POST.get('address', '')
            tenant.allow_email_notifications = request.POST.get('allow_email_notifications') == 'on'
            tenant.allow_sms_notifications = request.POST.get('allow_sms_notifications') == 'on'
            
            # Handle logo upload
            if request.FILES.get('logo'):
                tenant.logo = request.FILES['logo']
            
            tenant.save()
            print(f"Tenant updated successfully")
            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error updating tenant: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_POST
def create_razorpay_order(request, plan_id):
    """Create Razorpay order for subscription"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        plan = Plan.objects.get(id=plan_id)
        tenant = request.user.tenant

        # Check if tenant already has active subscription
        if tenant.status == 'active':
            return JsonResponse({'error': 'Tenant already has active subscription'}, status=400)

        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create order data
        order_data = {
            'amount': int(plan.price_monthly * 100),  # Amount in paisa
            'currency': 'INR',
            'payment_capture': '1'  # Auto capture
        }

        order = client.order.create(data=order_data)

        # Create payment transaction record
        PaymentTransaction.objects.create(
            tenant=tenant,
            razorpay_order_id=order['id'],
            amount=plan.price_monthly,
            status='created',
            plan=plan,
            billing_cycle='monthly'
        )

        return JsonResponse({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key': settings.RAZORPAY_KEY_ID
        })

    except Plan.DoesNotExist:
        return JsonResponse({'error': 'Plan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def payment_success(request):
    """Handle Razorpay payment success"""
    razorpay_order_id = request.GET.get('order_id')
    razorpay_payment_id = request.GET.get('payment_id')
    razorpay_signature = request.GET.get('signature')

    print(f"Payment callback received:")
    print(f"Order ID: {razorpay_order_id}")
    print(f"Payment ID: {razorpay_payment_id}")
    print(f"Signature: {razorpay_signature}")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        messages.error(request, 'Invalid payment parameters.')
        return redirect('company:subscription_plans')

    try:
        # Verify payment signature
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # Verify signature
        try:
            client.utility.verify_payment_signature(params_dict)
            print("Payment signature verified successfully")
        except Exception as verify_error:
            print(f"Signature verification failed: {verify_error}")
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('company:subscription_plans')

        # Get transaction
        transaction = PaymentTransaction.objects.get(
            razorpay_order_id=razorpay_order_id,
            tenant=request.user.tenant
        )
        
        print(f"Transaction found: {transaction.id}")
        
        # Update transaction
        transaction.razorpay_payment_id = razorpay_payment_id
        transaction.razorpay_signature = razorpay_signature
        transaction.status = 'paid'
        transaction.save()

        print(f"Transaction updated to paid status")

        # Activate tenant subscription
        tenant = request.user.tenant
        plan = transaction.plan
        from datetime import timedelta
        
        tenant.subscription_plan = plan
        tenant.subscription_start_date = timezone.now()
        tenant.subscription_end_date = timezone.now() + timedelta(days=30)  # Monthly subscription
        tenant.status = 'active'
        tenant.razorpay_payment_id = razorpay_payment_id
        tenant.razorpay_order_id = razorpay_order_id
        tenant.save()

        print(f"Tenant activated: {tenant.name} with plan {plan.name}")

        messages.success(request, f'🎉 Payment successful! Your {plan.name} subscription is now active. Welcome to HRM Dashboard!')
        return redirect('hrm_home')  # Redirect to HRM Dashboard

    except PaymentTransaction.DoesNotExist:
        print(f"Transaction not found for order: {razorpay_order_id}")
        messages.error(request, 'Transaction not found. Please contact support.')
        return redirect('company:subscription_plans')
    except Exception as e:
        print(f"Payment processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Payment processing failed: {str(e)}')
        return redirect('company:subscription_plans')


@login_required
def payment_cancel(request):
    """Handle payment cancel"""
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            transaction = PaymentTransaction.objects.get(
                razorpay_order_id=order_id,
                tenant=request.user.tenant
            )
            transaction.status = 'cancelled'
            transaction.save()
        except PaymentTransaction.DoesNotExist:
            pass

    messages.warning(request, 'Payment was cancelled.')
    return redirect('company:subscription_plans')


def logout_view(request):
    """Logs out the user and redirects to the login page."""
    logout(request)
    return redirect('company:login')