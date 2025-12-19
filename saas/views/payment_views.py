from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from saas.models.tenant import Tenant
from saas.models.plan import Plan
from saas.models import PaymentTransaction
from saas.models.subscription import Subscription
from saas.models.invoice import Invoice
from decimal import Decimal
import razorpay
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required(login_url='auth:login')
@csrf_exempt
def razorpay_payment(request):
    tenant_id = request.GET.get('tenant')
    billing_cycle = request.GET.get('cycle', 'monthly')
    # Only allow creating/processing orders for tenants whose subscription plan is active
    tenant = get_object_or_404(Tenant, id=tenant_id, subscription_plan__status=True)
    plan = tenant.subscription_plan
    if not plan:
        return redirect('/subscriptions/')

    # Determine amount based on billing cycle
    if billing_cycle == 'yearly':
        amount = int(plan.price_yearly * 100)
    else:
        amount = int(plan.price_monthly * 100)

    # Razorpay order creation
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': f'tenant_{tenant.id}',
        'payment_capture': 1
    }
    order = client.order.create(data=order_data)
    tenant.razorpay_order_id = order['id']
    tenant.save(update_fields=['razorpay_order_id'])

    # Create payment transaction record (store amount in rupees)
    try:
        tx_amount = (Decimal(amount) / Decimal(100))
    except Exception:
        tx_amount = Decimal('0.00')
    PaymentTransaction.objects.create(
        tenant=tenant,
        plan=plan,
        razorpay_order_id=order['id'],
        amount=tx_amount,
        currency='INR',
        status='CREATED',
    )

    context = {
        'tenant': tenant,
        'plan': plan,
        'razorpay_order_id': order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'callback_url': '/payment/razorpay/verify/'
    }
    return render(request, 'payment/razorpay_payment.html', context)

@login_required(login_url='auth:login')
@csrf_exempt
def razorpay_verify(request):
    if request.method == 'POST':
        import hmac, hashlib
        data = request.POST
        tenant_id = data.get('tenant_id')
        payment_id = data.get('razorpay_payment_id')
        order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')
        tenant = get_object_or_404(Tenant, id=tenant_id)
        # Verify signature
        key_secret = settings.RAZORPAY_KEY_SECRET
        msg = f"{order_id}|{payment_id}".encode()
        generated_signature = hmac.new(key_secret.encode(), msg, hashlib.sha256).hexdigest()
        if generated_signature == signature:
            # Activate tenant
            tenant.status = 'active'
            tenant.subscription_start_date = timezone.now()
            # Use default 30 days for monthly billing, 365 for yearly
            tenant.subscription_end_date = tenant.subscription_start_date + timedelta(days=30)
            tenant.razorpay_payment_id = payment_id
            tenant.razorpay_order_id = order_id
            tenant.save()

            # Update payment transaction record if exists
            try:
                tx = PaymentTransaction.objects.filter(razorpay_order_id=order_id).first()
                if tx:
                    tx.razorpay_payment_id = payment_id
                    tx.status = 'PAID'
                    tx.save(update_fields=['razorpay_payment_id', 'status', 'updated_at'])
                    # Create a Subscription record for this tenant if not present
                    try:
                        # use tx.amount (Decimal) and tenant subscription dates
                        start_date = tenant.subscription_start_date.date() if tenant.subscription_start_date else timezone.now().date()
                        end_date = tenant.subscription_end_date.date() if tenant.subscription_end_date else None
                        billing_cycle = 'monthly'
                        Subscription.objects.create(
                            tenant=tenant,
                            plan=tx.plan or tenant.subscription_plan,
                            start_date=start_date,
                            end_date=end_date if end_date else start_date,
                            billing_cycle=billing_cycle,
                            amount=tx.amount,
                            status='active'
                        )
                    except Exception:
                        pass
            except Exception:
                pass
            return JsonResponse({'success': True, 'redirect_url': f'/tenant/success/?tenant={tenant.id}'})
        else:
            return JsonResponse({'success': False, 'error': 'Payment verification failed.'})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def orders_list(request):
    """Admin view: list tenants whose subscription plan is active.

    Each tenant row provides a Pay/Renew link to the razorpay payment flow.
    """
    # List subscriptions so each row corresponds to a subscription record
    subscriptions = Subscription.objects.select_related('tenant', 'plan').order_by('-created_at')
    # fallback to tenants with active subscription_plan if no Subscription records exist
    tenants = Tenant.objects.filter(subscription_plan__status=True).order_by('name')
    return render(request, 'payment/orders_list.html', {'subscriptions': subscriptions, 'tenants': tenants})


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def order_detail(request, tenant_id):
    """Admin view: show subscription details for a specific tenant/company."""
    tenant = get_object_or_404(Tenant, id=tenant_id)
    plan = tenant.subscription_plan
    # Optionally include recent transactions
    transactions = PaymentTransaction.objects.filter(tenant=tenant).order_by('-created_at')[:10]
    context = {
        'tenant': tenant,
        'plan': plan,
        'transactions': transactions,
    }
    return render(request, 'payment/order_detail.html', context)


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def subscription_detail(request, subscription_id):
    """Admin view: show details for a specific subscription record."""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    context = {
        'subscription': subscription,
    }
    return render(request, 'payment/subscription_detail.html', context)


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def invoices_list(request):
    """Admin view: list payment transactions (invoices)."""
    # Prefer Invoice records; fallback to PaymentTransaction if none exist
    invoices = Invoice.objects.select_related('tenant', 'subscription').order_by('-created_at')
    if invoices.exists():
        return render(request, 'payment/invoices_list.html', {'invoices': invoices})
    transactions = PaymentTransaction.objects.select_related('tenant', 'plan').order_by('-created_at')
    return render(request, 'payment/invoices_list.html', {'transactions': transactions})


@login_required(login_url='auth:login')
@user_passes_test(lambda u: u.is_staff)
def payments_list(request):
    """Admin view: show all PaymentTransaction records."""
    transactions = PaymentTransaction.objects.select_related('tenant', 'plan').order_by('-created_at')
    return render(request, 'payment/payments_list.html', {'transactions': transactions})
