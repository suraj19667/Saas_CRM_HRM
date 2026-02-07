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
import hmac
import hashlib
import json
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum

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
    # Get filter parameters
    date_filter = request.GET.get('date')
    plan_filter = request.GET.get('plan')
    status_filter = request.GET.get('status')
    sort_filter = request.GET.get('sort')
    search_query = request.GET.get('search')
    per_page = int(request.GET.get('per_page', 10))

    # Base queryset
    subscriptions_queryset = Subscription.objects.select_related('tenant', 'plan').order_by('-created_at')

    # Apply filters
    if date_filter:
        subscriptions_queryset = subscriptions_queryset.filter(created_at__date=date_filter)
    
    if plan_filter:
        if plan_filter == 'basic_monthly':
            subscriptions_queryset = subscriptions_queryset.filter(plan__name__icontains='basic', billing_cycle='monthly')
        elif plan_filter == 'basic_yearly':
            subscriptions_queryset = subscriptions_queryset.filter(plan__name__icontains='basic', billing_cycle='yearly')
        elif plan_filter == 'advanced_monthly':
            subscriptions_queryset = subscriptions_queryset.filter(plan__name__icontains='advanced', billing_cycle='monthly')
        elif plan_filter == 'advanced_yearly':
            subscriptions_queryset = subscriptions_queryset.filter(plan__name__icontains='advanced', billing_cycle='yearly')
        elif plan_filter == 'enterprise_monthly':
            subscriptions_queryset = subscriptions_queryset.filter(plan__name__icontains='enterprise', billing_cycle='monthly')
        elif plan_filter == 'enterprise_yearly':
            subscriptions_queryset = subscriptions_queryset.filter(plan__name__icontains='enterprise', billing_cycle='yearly')

    if status_filter:
        subscriptions_queryset = subscriptions_queryset.filter(status=status_filter)

    if search_query:
        subscriptions_queryset = subscriptions_queryset.filter(
            tenant__name__icontains=search_query
        )

    # Apply sorting
    if sort_filter:
        days = int(sort_filter)
        date_threshold = timezone.now() - timedelta(days=days)
        subscriptions_queryset = subscriptions_queryset.filter(created_at__gte=date_threshold)

    # Get paginated results
    from django.core.paginator import Paginator
    paginator = Paginator(subscriptions_queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare subscription data for template
    subscriptions_data = []
    for subscription in page_obj:
        # Get employee count (users in this tenant)
        employee_count = subscription.tenant.users.count()
        max_employees = getattr(subscription.plan, 'max_users', 100) if subscription.plan else 100
        employee_percent = min((employee_count / max_employees) * 100, 100) if max_employees > 0 else 0

        # Get admin email (first user or user with admin role)
        admin_email = ''
        admin_user = subscription.tenant.users.filter(is_staff=True).first()
        if not admin_user:
            admin_user = subscription.tenant.users.first()
        if admin_user:
            admin_email = admin_user.email

        subscription_data = {
            'id': subscription.id,
            'date': subscription.created_at.date(),
            'name': subscription.tenant.name,
            'avatar_url': subscription.tenant.logo.url if subscription.tenant.logo and subscription.tenant.logo.name else None,
            'status': subscription.status.title(),
            'plan': f"{subscription.plan.name} ({subscription.billing_cycle})" if subscription.plan else "No Plan",
            'employees': employee_count,
            'employee_percent': employee_percent,
            'admin_email': admin_email,
            'last_activity': subscription.updated_at.strftime('%d/%m/%Y %H:%M') if subscription.updated_at else 'N/A',
        }
        subscriptions_data.append(subscription_data)

    # Calculate stats
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    total_companies = Tenant.objects.count()
    
    # Mock growth data (you can calculate real growth)
    companies_growth = "+2.1%"
    subscriptions_growth = "+2.1%"
    revenue_growth = "+2.1%"
    trials_growth = "+2.1%"
    
    # Calculate revenue (sum of amounts from subscriptions)
    monthly_revenue = Subscription.objects.filter(status='active').aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'subscriptions': subscriptions_data,
        'page_obj': page_obj,
        'total_companies': total_companies,
        'active_subscriptions': active_subscriptions,
        'monthly_revenue': f"₹{monthly_revenue:,.0f}L" if monthly_revenue >= 100000 else f"₹{monthly_revenue:,.0f}",
        'active_trials': 25,  # Mock data
        'companies_growth': companies_growth,
        'subscriptions_growth': subscriptions_growth,
        'revenue_growth': revenue_growth,
        'trials_growth': trials_growth,
        'request': request,
    }
    
    return render(request, 'subscription_list.html', context)


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


@login_required(login_url='auth:login')
@csrf_exempt
def create_razorpay_order(request):
    """Create Razorpay order for HRM customer subscription"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        # Get plan
        plan = get_object_or_404(Plan, id=plan_id, status=True)
        
        # Get or create tenant for user
        user = request.user
        tenant = None
        if hasattr(user, 'tenant') and user.tenant:
            tenant = user.tenant
        elif hasattr(user, 'company_profile') and user.company_profile:
            tenant = user.company_profile
        
        if not tenant:
            return JsonResponse({'success': False, 'error': 'No tenant associated with user'})
        
        # Calculate amount based on billing cycle
        if billing_cycle == 'yearly':
            amount = int(plan.price_yearly * 100)  # Convert to paisa
        else:
            amount = int(plan.price_monthly * 100)
        
        # Initialize Razorpay client securely
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create order
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'order_rcptid_{tenant.id}_{timezone.now().timestamp()}',
            'payment_capture': 1
        }
        
        order = client.order.create(data=order_data)
        
        # Create payment transaction record
        transaction = PaymentTransaction.objects.create(
            tenant=tenant,
            plan=plan,
            razorpay_order_id=order['id'],
            amount=Decimal(amount) / Decimal(100),  # Convert back to rupees
            currency='INR',
            billing_cycle=billing_cycle,
            status='created'
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order['id'],
            'amount': amount,
            'key_id': settings.RAZORPAY_KEY_ID
        })
        
    except Plan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plan not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='auth:login')
@csrf_exempt
def verify_razorpay_payment(request):
    """Verify Razorpay payment signature and activate subscription"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Verify signature
        key_secret = settings.RAZORPAY_KEY_SECRET
        msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
        generated_signature = hmac.new(key_secret.encode(), msg, hashlib.sha256).hexdigest()
        
        if generated_signature != razorpay_signature:
            return JsonResponse({'success': False, 'error': 'Invalid signature'})
        
        # Get transaction
        transaction = PaymentTransaction.objects.get(razorpay_order_id=razorpay_order_id)
        
        # Update transaction
        transaction.razorpay_payment_id = razorpay_payment_id
        transaction.razorpay_signature = razorpay_signature
        transaction.status = 'paid'
        transaction.save()
        
        # Get tenant
        tenant = transaction.tenant
        
        # Calculate subscription dates
        start_date = timezone.now().date()
        if transaction.billing_cycle == 'yearly':
            end_date = start_date + timedelta(days=365)
        else:
            end_date = start_date + timedelta(days=30)
        
        # Create or update subscription
        Subscription.objects.filter(tenant=tenant, status='active').update(status='expired')
        
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=transaction.plan,
            start_date=start_date,
            end_date=end_date,
            billing_cycle=transaction.billing_cycle,
            amount=transaction.amount,
            status='active'
        )
        
        # Update tenant subscription info
        tenant.subscription_plan = transaction.plan
        tenant.subscription_start_date = timezone.now()
        tenant.subscription_end_date = timezone.datetime.combine(end_date, timezone.datetime.min.time())
        tenant.status = 'active'
        tenant.save()
        
        # Create invoice
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{tenant.id}"
        Invoice.objects.create(
            tenant=tenant,
            subscription=subscription,
            invoice_number=invoice_number,
            amount=transaction.amount,
            due_date=end_date,
            status='paid'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Payment verified and subscription activated'
        })
        
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Transaction not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
