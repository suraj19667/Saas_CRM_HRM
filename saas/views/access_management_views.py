"""
Access Management View - Combined Roles & Permissions Management
Allows managing both roles and permissions on a single page.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.utils import timezone

from ..models import Role, Permission, RolePermission
from saas.forms.tenant_forms import TenantForm
from saas.models import Tenant, PaymentTransaction


@login_required
def access_management(request):
    """
    Combined view for managing roles and permissions on a single page.

    Returns:
        HttpResponse: Rendered template with roles and permissions data
    """
    # Fetch roles with optimized queries
    roles_queryset = Role.objects.prefetch_related(
        Prefetch(
            'role_permissions',
            queryset=RolePermission.objects.select_related('permission')
        )
    ).annotate(
        permission_count=Count('role_permissions', distinct=True),
        user_count=Count('user_roles', distinct=True)
    ).order_by('name')

    # Fetch permissions with optimized queries
    permissions_queryset = Permission.objects.prefetch_related(
        Prefetch(
            'permission_roles',
            queryset=RolePermission.objects.select_related('role')
        )
    ).annotate(
        role_count=Count('permission_roles', distinct=True)
    ).order_by('module', 'name')

    # Group permissions by module
    permissions_by_module = {}
    for permission in permissions_queryset:
        module = permission.module or 'General'
        if module not in permissions_by_module:
            permissions_by_module[module] = []
        permissions_by_module[module].append(permission)

    context = {
        'roles': roles_queryset,
        'permissions': permissions_queryset,
        'permissions_by_module': permissions_by_module,
        'total_roles': roles_queryset.count(),
        'total_permissions': permissions_queryset.count(),
    }

    return render(request, 'access_management.html', context)


def subscribe_tenant(request):
    if request.method == "POST":
        form = TenantForm(request.POST, request.FILES)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.status = "inactive"
            tenant.save()

            # Create Razorpay order
            plan = tenant.subscription_plan
            razorpay_order = razorpay_client.order.create({
                "amount": int(plan.price * 100),  # Convert to paisa
                "currency": "INR",
                "payment_capture": 1,
            })

            # Save payment transaction
            PaymentTransaction.objects.create(
                tenant=tenant,
                plan=plan,
                razorpay_order_id=razorpay_order["id"],
                amount=plan.price,
                currency="INR",
                status="CREATED",
            )

            # Redirect to Razorpay checkout
            return render(request, "company/razorpay_checkout.html", {
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_api_key": RAZORPAY_API_KEY,
                "tenant": tenant,
            })
    else:
        form = TenantForm()
    return render(request, "company/subscribe_tenant.html", {"form": form})


def subscribe_now(request):
    """Handles tenant subscription form and redirects to Razorpay checkout."""
    tenant = getattr(request, 'tenant', None)

    if request.method == "POST":
        form = TenantForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.status = "inactive"
            tenant.save()

            # Create Razorpay order
            plan = tenant.subscription_plan
            razorpay_order = razorpay_client.order.create({
                "amount": int(plan.price * 100),  # Convert to paisa
                "currency": "INR",
                "payment_capture": 1,
            })

            # Save payment transaction
            PaymentTransaction.objects.create(
                tenant=tenant,
                plan=plan,
                razorpay_order_id=razorpay_order["id"],
                amount=plan.price,
                currency="INR",
                status="CREATED",
            )

            # Redirect to Razorpay checkout
            return render(request, "company/razorpay_checkout.html", {
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_api_key": RAZORPAY_API_KEY,
                "tenant": tenant,
            })
    else:
        form = TenantForm(instance=tenant)

    return render(request, "company/subscribe_tenant.html", {"form": form})


def payment_success_handler(request, razorpay_payment_id):
    transaction = get_object_or_404(PaymentTransaction, razorpay_payment_id=razorpay_payment_id)
    tenant = transaction.tenant

    # Update transaction status
    transaction.status = "PAID"
    transaction.save()

    # Update tenant details
    tenant.status = "active"
    tenant.subscription_start_date = timezone.now()
    tenant.subscription_end_date = timezone.now() + transaction.plan.duration
    tenant.save()

    # Redirect to tenant dashboard
    return redirect(reverse("tenant_dashboard", kwargs={"tenant_slug": tenant.slug}))
