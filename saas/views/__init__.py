from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q, Count
import random
import string
from ..models import CustomUser, Role, Permission, RolePermission, Tenant, Subscription
from ..forms import CustomUserRegistrationForm, CustomLoginForm, OTPVerificationForm, CustomUserChangeForm
from ..decorators import permission_required

# Helper function for user_passes_test decorator
def is_staff_user(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser

# ==================== DASHBOARD VIEWS ====================
@login_required(login_url='auth:login')
@never_cache
@ensure_csrf_cookie
def deshboard_view(request):
    """
    Main dashboard view - redirects to admin or tenant dashboard based on user type
    """
    if not request.user.is_authenticated:
        return redirect('auth:login')
    
    # Check if user is admin/staff
    if request.user.is_superuser or request.user.is_staff:
        return admin_dashboard_view(request)
    else:
        return tenant_dashboard_view(request)


@login_required(login_url='auth:login')
@user_passes_test(is_staff_user, login_url='dashboard')
@never_cache
@ensure_csrf_cookie
def admin_dashboard_view(request):
    """
    Admin dashboard view - shows system-wide statistics
    """
    from ..models import CustomUser, Role, Plan, Feature
    
    # System-wide stats for admin
    total_users = CustomUser.objects.count()
    total_tenants = Tenant.objects.count()
    total_subscriptions = Subscription.objects.filter(status='active').count()
    total_plans = Plan.objects.count()
    
    # Recent activity
    recent_users = CustomUser.objects.select_related('tenant').order_by('-created_at')[:10]
    recent_tenants = Tenant.objects.order_by('-created_at')[:10]
    active_subscriptions = Subscription.objects.filter(status='active').select_related('tenant', 'plan')[:10]
    
    # Get all plans with their features
    all_plans = Plan.objects.prefetch_related('plan_features__feature').order_by('price_monthly')
    
    response = render(request, 'overview.html', {
        'total_users': total_users,
        'total_tenants': total_tenants, 
        'total_subscriptions': total_subscriptions,
        'total_plans': total_plans,
        'recent_users': recent_users,
        'recent_tenants': recent_tenants,
        'active_subscriptions': active_subscriptions,
        'all_plans': all_plans,
        'is_admin': True
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required(login_url='auth:login')
@never_cache
@ensure_csrf_cookie
def tenant_dashboard_view(request):
    """
    Tenant dashboard view - shows features and plan information
    """
    from ..models import CustomUser, Role, Plan, Feature, PlanFeature
    
    # Use request.tenant if set (subdomain), otherwise use user's tenant
    tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
    
    if not tenant:
        messages.error(request, 'No tenant found. Please contact administrator.')
        # Render an informational page instead of redirecting to the login
        # This avoids a redirect loop where the authenticated user is sent
        # to the login page which then redirects back to the dashboard.
        return render(request, 'no_tenant.html', {
            'message': 'Your account is not associated with any company. Please contact the administrator.'
        })
    
    # Tenant specific data
    users = CustomUser.objects.filter(tenant=tenant).select_related('role')
    roles = Role.objects.filter(tenant=tenant).prefetch_related('users')
    
    # Get current subscription and plan
    current_subscription = Subscription.objects.filter(
        tenant=tenant,
        status='active'
    ).select_related('plan').first()
    
    current_plan = current_subscription.plan if current_subscription else None
    
    # Get plan features
    plan_features = []
    all_features = []
    excluded_features = []
    
    if current_plan:
        # Get features included in current plan
        plan_features = PlanFeature.objects.filter(
            plan=current_plan
        ).select_related('feature').order_by('feature__name')
        
        # Get IDs of features included in current plan
        included_feature_ids = plan_features.values_list('feature_id', flat=True)
        
        # Get all available features for comparison
        all_features = Feature.objects.all().order_by('name')
        
        # Get features not included in current plan
        excluded_features = Feature.objects.exclude(
            id__in=included_feature_ids
        ).order_by('name')
    
    # Get available plans for upgrade options
    available_plans = Plan.objects.filter(status=True).order_by('price_monthly')
    
    response = render(request, 'tenant_dashboard.html', {
        'users': users,
        'roles': roles,
        'current_subscription': current_subscription,
        'current_plan': current_plan,
        'plan_features': plan_features,
        'all_features': all_features,
        'excluded_features': excluded_features,
        'available_plans': available_plans,
        'tenant': tenant,
        'total_users': users.count(),
        'total_roles': roles.count(),
        'is_tenant': True
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def base_view(request):
    """
    Base view to render the base template
    """
    from ..models import CustomUser, Role
    users = CustomUser.objects.select_related('role').all()
    roles = Role.objects.prefetch_related('users').all()
    return render(request, 'base.html', {'users': users, 'roles': roles})


# ==================== REGISTRATION VIEW ====================
@never_cache
def register_view(request):
    """
    User registration with OTP verification
    """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            # Store user data in session temporarily
            request.session['pending_user_data'] = {
                'username': form.cleaned_data.get('username') or form.cleaned_data['email'].split('@')[0],
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'password': form.cleaned_data['password1'],
            }
            
            # Generate and store OTP
            otp = ''.join(random.choices(string.digits, k=6))
            request.session['pending_otp'] = otp
            request.session['otp_created_at'] = timezone.now().isoformat()
            
            # Send OTP email
            try:
                send_otp_email_temp(
                    form.cleaned_data['email'],
                    form.cleaned_data['first_name'],
                    form.cleaned_data['last_name'],
                    otp
                )
                messages.success(request, f'Registration successful! OTP sent to {form.cleaned_data["email"]}')
            except Exception as e:
                messages.warning(request, f'Registration successful! OTP could not be sent due to email error. Please contact support. OTP: {otp}')
            
            return redirect('verify_otp')
    else:
        form = CustomUserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})


# ==================== OTP VERIFICATION VIEW ====================
@never_cache
def verify_otp_view(request):
    """
    Verify OTP and create user account
    """
    pending_user_data = request.session.get('pending_user_data')
    pending_otp = request.session.get('pending_otp')
    otp_created_at = request.session.get('otp_created_at')
    
    if not pending_user_data or not pending_otp:
        messages.error(request, 'No pending verification found. Please register first.')
        return redirect('auth:register')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            # Check if OTP is expired (10 minutes)
            otp_time = timezone.datetime.fromisoformat(otp_created_at)
            if timezone.now() > otp_time + timezone.timedelta(minutes=10):
                messages.error(request, 'OTP has expired. Please request a new one.')
            elif entered_otp == pending_otp:
                # Create user in database
                user = CustomUser.objects.create_user(
                    email=pending_user_data['email'],
                    password=pending_user_data['password'],
                    username=pending_user_data['username'],
                    first_name=pending_user_data['first_name'],
                    last_name=pending_user_data['last_name'],
                    is_active=True,
                    is_verified=True
                )
                
                # Clear session data
                del request.session['pending_user_data']
                del request.session['pending_otp']
                del request.session['otp_created_at']
                
                # Log the user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Email verified successfully! Welcome!')
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'auth/verify_otp.html', {
        'form': form,
        'email': pending_user_data['email']
    })


# ==================== RESEND OTP VIEW ====================
@never_cache
def resend_otp_view(request):
    """
    Resend OTP to user's email
    """
    pending_user_data = request.session.get('pending_user_data')
    if not pending_user_data:
        messages.error(request, 'No pending verification found.')
        return redirect('register')
    
    # Generate new OTP
    otp = ''.join(random.choices(string.digits, k=6))
    request.session['pending_otp'] = otp
    request.session['otp_created_at'] = timezone.now().isoformat()
    
    # Send OTP email
    send_otp_email_temp(
        pending_user_data['email'],
        pending_user_data['first_name'],
        pending_user_data['last_name'],
        otp
    )
    
    messages.success(request, f'New OTP sent to {pending_user_data["email"]}')
    return redirect('verify_otp')


# ==================== SEND OTP EMAIL ====================
def send_otp_email_temp(email, first_name, last_name, otp):
    """
    Send OTP via email
    """
    subject = 'Verify Your Email - OTP Code'
    message = f'''
Hello {first_name} {last_name},

Thank you for registering! Your OTP for email verification is:

{otp}

This OTP will expire in 5 minutes.

If you didn't request this, please ignore this email.

Best regards,
Authentication Team
    '''
    
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )


# ==================== LOGIN VIEW ====================
@never_cache
def login_view(request):
    """
    User login with email and password
    """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Authenticate user (our custom backend handles email/username)
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Check if user belongs to this tenant (if tenant exists)
                if hasattr(request, 'tenant') and request.tenant:
                    if user.tenant != request.tenant:
                        messages.error(request, 'Access denied - user does not belong to this tenant.')
                        return redirect(settings.LOGIN_URL)
                # For no tenant, allow any user (super admin)
                
                # Check if user is verified
                if hasattr(user, 'is_verified') and not user.is_verified:
                    messages.error(request, 'Please verify your email first.')
                    return redirect(settings.LOGIN_URL)
                
                # Login user
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                next_url = request.GET.get('next') or settings.LOGIN_REDIRECT_URL
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username/email or password. Please try again.')
                return redirect(settings.LOGIN_URL)
    else:
        form = CustomLoginForm()
    
    # Choose template based on tenant
    template = 'auth/tenant_login.html' if (hasattr(request, 'tenant') and request.tenant) else 'auth/login.html'
    context = {'form': form}
    if hasattr(request, 'tenant') and request.tenant:
        context['tenant'] = request.tenant
    
    response = render(request, template, context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# ==================== REGISTER VIEW ====================
@never_cache
def register_view(request):
    """
    User registration
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if hasattr(request, 'tenant') and request.tenant:
                user.tenant = request.tenant
            user.is_verified = True  # Auto-verify
            user.save()
            
            # Auto-login only if the user is associated with a tenant (tenant users go to dashboard)
            if getattr(user, 'tenant', None):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome {user.get_full_name()}! Your account has been created.')
                return redirect('dashboard')
            else:
                # For users without a tenant, do not auto-login. Redirect to login page.
                messages.success(request, 'Account created successfully. Please login to continue.')
                return redirect('auth:login')
    else:
        form = CustomUserRegistrationForm()
    
    # Choose template based on tenant
    template = 'auth/tenant_register.html' if (hasattr(request, 'tenant') and request.tenant) else 'auth/register.html'
    context = {'form': form}
    if hasattr(request, 'tenant') and request.tenant:
        context['tenant'] = request.tenant
    
    response = render(request, template, context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# ==================== LOGOUT VIEW ====================
@require_http_methods(["GET", "POST"])
@never_cache
@ensure_csrf_cookie
def logout_view(request):

    if request.method == 'POST':
        logout(request)
        request.session.flush()
        
        # Clear all existing messages before adding logout message
        storage = messages.get_messages(request)
        storage.used = True
        
        messages.success(request, 'You have been logged out successfully.')
        
        response = redirect('auth:login')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['Clear-Site-Data'] = '"cache", "cookies", "storage"'
        return response
    
    return redirect('auth:login')


# ==================== CRM MENU VIEWS ====================
@login_required(login_url='auth:login')
@never_cache
def leads_view(request):
    """Leads page view"""
    return render(request, 'crm/leads.html')


@login_required(login_url='auth:login')
@never_cache
def deals_view(request):
    """Deals page view"""
    return render(request, 'crm/deals.html')


@login_required(login_url='auth:login')
@never_cache
def form_builder_view(request):
    """Form Builder page view"""
    return render(request, 'crm/form_builder.html')


@login_required(login_url='auth:login')
@never_cache
def contract_view(request):
    """Contract page view"""
    return render(request, 'crm/contract.html')


@login_required(login_url='auth:login')
@never_cache
def crm_setup_view(request):
    """
    CRM setup page with user management
    """
    return render(request, 'crm/crm_setup.html')


# ==================== USER MANAGEMENT API VIEWS ====================
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import user_passes_test
import json

def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='auth:login')
@permission_required('view_user', raise_exception=True)
@require_http_methods(["GET"])
def api_users_list(request):
    """
    API endpoint to list all users
    """
    try:
        users = CustomUser.objects.select_related('role').all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'phone': user.phone,
                'role': user.role.name if user.role else 'No Role',
                'role_id': user.role.id if user.role else None,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_verified': user.is_verified,
                'date_joined': user.date_joined.strftime('%Y-%m-%d'),
            })
        
        return JsonResponse({'success': True, 'users': users_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@permission_required('create_user', raise_exception=True)
@require_POST
def api_user_create(request):
    """
    API endpoint to create a new user
    """
    try:
        data = json.loads(request.body)
        
        # Check if username or email already exists
        if CustomUser.objects.filter(username=data.get('username')).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists'}, status=400)
        
        if CustomUser.objects.filter(email=data.get('email')).exists():
            return JsonResponse({'success': False, 'error': 'Email already exists'}, status=400)
        
        # Get role if provided
        role = None
        if data.get('role_id'):
            try:
                role = Role.objects.get(id=data.get('role_id'))
            except Role.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid role'}, status=400)
        
        # Create user
        user = CustomUser.objects.create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', ''),
            is_active=data.get('is_active', True),
            is_staff=data.get('is_staff', False),
            is_verified=True,
            role=role
        )
        
        return JsonResponse({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@permission_required('edit_user', raise_exception=True)
@require_POST
def api_user_update(request, user_id):
    """
    API endpoint to update a user
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken by another user
            if CustomUser.objects.filter(email=data['email']).exclude(id=user_id).exists():
                return JsonResponse({'success': False, 'error': 'Email already exists'}, status=400)
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_staff' in data:
            user.is_staff = data['is_staff']
        if 'role_id' in data:
            try:
                user.role = Role.objects.get(id=data['role_id']) if data['role_id'] else None
            except Role.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid role'}, status=400)
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'role': user.role.name if user.role else 'No Role',
            }
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@permission_required('delete_user', raise_exception=True)
@require_POST
def api_user_delete(request, user_id):
    """
    API endpoint to delete a user
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Prevent deleting own account or superuser
        if user.id == request.user.id:
            return JsonResponse({'success': False, 'error': 'Cannot delete your own account'}, status=400)
        
        if user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Cannot delete superuser'}, status=400)
        
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== ROLE MANAGEMENT API VIEWS ====================

@login_required(login_url='auth:login')
@require_http_methods(["GET"])
def api_roles_list(request):
    """
    API endpoint to list all roles
    """
    try:
        roles = Role.objects.prefetch_related('role_permissions__permission', 'users').all()
        roles_data = []
        
        for role in roles:
            permissions = [
                {
                    'id': rp.permission.id,
                    'name': rp.permission.name,
                    'codename': rp.permission.codename,
                    'module': rp.permission.module,
                }
                for rp in role.role_permissions.select_related('permission').all()
            ]
            
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'user_count': role.users.count(),
                'permissions': permissions,
                'created_at': role.created_at.strftime('%Y-%m-%d'),
            })
        
        return JsonResponse({'success': True, 'roles': roles_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@require_POST
@user_passes_test(is_staff_user, login_url='dashboard')
def api_role_create(request):
    """
    API endpoint to create a new role
    """
    try:
        data = json.loads(request.body)
        
        # Check if role name already exists
        if Role.objects.filter(name=data.get('name')).exists():
            return JsonResponse({'success': False, 'error': 'Role name already exists'}, status=400)
        
        # Create role
        role = Role.objects.create(
            name=data.get('name'),
            description=data.get('description', '')
        )
        
        # Add permissions
        if 'permission_ids' in data:
            for perm_id in data['permission_ids']:
                try:
                    permission = Permission.objects.get(id=perm_id)
                    RolePermission.objects.create(role=role, permission=permission)
                except Permission.DoesNotExist:
                    pass
        
        return JsonResponse({
            'success': True,
            'message': 'Role created successfully',
            'role': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@require_POST
@user_passes_test(is_staff_user, login_url='dashboard')
def api_role_update(request, role_id):
    """
    API endpoint to update a role
    """
    try:
        role = Role.objects.get(id=role_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'name' in data:
            # Check if name is already taken by another role
            if Role.objects.filter(name=data['name']).exclude(id=role_id).exists():
                return JsonResponse({'success': False, 'error': 'Role name already exists'}, status=400)
            role.name = data['name']
        
        if 'description' in data:
            role.description = data['description']
        
        role.save()
        
        # Update permissions if provided
        if 'permission_ids' in data:
            # Remove existing permissions
            RolePermission.objects.filter(role=role).delete()
            
            # Add new permissions
            for perm_id in data['permission_ids']:
                try:
                    permission = Permission.objects.get(id=perm_id)
                    RolePermission.objects.create(role=role, permission=permission)
                except Permission.DoesNotExist:
                    pass
        
        return JsonResponse({
            'success': True,
            'message': 'Role updated successfully',
            'role': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
            }
        })
    except Role.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Role not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@require_POST
@user_passes_test(is_staff_user, login_url='dashboard')
def api_role_delete(request, role_id):
    """
    API endpoint to delete a role
    """
    try:
        role = Role.objects.get(id=role_id)
        
        # Check if role is assigned to any users
        if role.users.exists():
            return JsonResponse({
                'success': False,
                'error': f'Cannot delete role. It is assigned to {role.users.count()} user(s)'
            }, status=400)
        
        role_name = role.name
        role.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Role {role_name} deleted successfully'
        })
    except Role.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Role not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== PERMISSION MANAGEMENT API VIEWS ====================

@login_required(login_url='auth:login')
@require_http_methods(["GET"])
@user_passes_test(is_staff_user, login_url='dashboard')
def api_permissions_list(request):
    """
    API endpoint to list all permissions
    """
    try:
        permissions = Permission.objects.all().order_by('module', 'name')
        permissions_data = []
        
        for perm in permissions:
            permissions_data.append({
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'description': perm.description,
                'module': perm.module,
                'created_at': perm.created_at.strftime('%Y-%m-%d'),
            })
        
        # Group by module
        modules = {}
        for perm in permissions_data:
            module = perm['module']
            if module not in modules:
                modules[module] = []
            modules[module].append(perm)
        
        return JsonResponse({
            'success': True,
            'permissions': permissions_data,
            'modules': modules
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@require_POST
@user_passes_test(is_staff_user, login_url='dashboard')
def api_permission_create(request):
    """
    API endpoint to create a new permission
    """
    try:
        data = json.loads(request.body)
        
        # Check if permission codename already exists
        if Permission.objects.filter(codename=data.get('codename')).exists():
            return JsonResponse({'success': False, 'error': 'Permission codename already exists'}, status=400)
        
        # Create permission
        permission = Permission.objects.create(
            name=data.get('name'),
            codename=data.get('codename'),
            description=data.get('description', ''),
            module=data.get('module', 'general')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Permission created successfully',
            'permission': {
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def users_list(request):
    """
    View to list all users
    """
    if not request.user.is_authenticated:
        return redirect('auth:login')
    
    # Check if this is admin users page
    is_admin_page = 'admin' in request.path
    
    if is_admin_page:
        # Filter for admin users (superusers or users with Admin role)
        users_queryset = CustomUser.objects.select_related('role').filter(
            Q(is_superuser=True) | Q(role__name='Admin')
        )
        page_title = 'Admin Users'
        template = 'saas/admin_user.html'
    else:
        # For "All Users" page, show tenants/companies
        tenants_queryset = Tenant.objects.select_related('subscription_plan').prefetch_related('users').all()
        page_title = 'All Users'
        template = 'users/users_list.html'
        
        # Prepare tenant data for template
        tenants = []
        for tenant in tenants_queryset:
            # Get admin user (first user or superuser)
            admin_user = tenant.users.filter(is_superuser=True).first() or tenant.users.first()
            admin_email = admin_user.email if admin_user else 'N/A'
            
            # Employee count (total users in tenant)
            employee_count = tenant.users.count()
            # Assuming plan has employee limit
            plan_limit = tenant.subscription_plan.max_users if tenant.subscription_plan else 100
            employee_percentage = (employee_count / plan_limit * 100) if plan_limit > 0 else 0
            
            tenants.append({
                'id': tenant.id,
                'created': tenant.created_at,
                'name': tenant.name,
                'status': 'Active' if tenant.status == 'active' else ('Trial' if tenant.status == 'inactive' else tenant.status.title()),
                'plan': tenant.subscription_plan.name if tenant.subscription_plan else 'No Plan',
                'employee_count': employee_count,
                'employee_limit': plan_limit,
                'employee_percentage': employee_percentage,
                'admin_email': admin_email,
                'last_activity': tenant.updated_at,
                'domain': tenant.domain,
            })
        
        # Stats for cards
        total_companies = tenants_queryset.count()
        active_subscriptions = tenants_queryset.filter(status='active').count()
        # Monthly revenue calculation (simplified)
        monthly_revenue = sum(
            tenant.subscription_plan.price_monthly if tenant.subscription_plan and tenant.status == 'active' else 0
            for tenant in tenants_queryset
        )
        active_trials = tenants_queryset.filter(status='inactive').count()
        
        return render(request, template, {
            'tenants': tenants,
            'total_companies': total_companies,
            'active_subscriptions': active_subscriptions,
            'monthly_revenue': monthly_revenue,
            'active_trials': active_trials,
            'page_title': page_title
        })
    
    # Prepare users data for template (for admin page)
    users = []
    for user in users_queryset:
        permissions_count = user.role.role_permissions.count() if user.role else 0
        users.append({
            'id': user.id,
            'created': user.created_at,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'role': user.role.name if user.role else 'No Role',
            'permissions': permissions_count,
            'last_login': user.last_login,
        })
    
    # Prepare roles data with counts
    roles_queryset = Role.objects.prefetch_related('users').all()
    roles = []
    for role in roles_queryset:
        # Assuming a default limit of 10 for now, or you can get from plan
        limit = 10  # You can make this dynamic based on subscription
        roles.append({
            'name': role.name,
            'count': role.user_count,
            'limit': limit,
        })
    
    return render(request, template, {
        'users': users, 
        'roles': roles,
        'is_admin_page': is_admin_page,
        'page_title': page_title
    })


@login_required
def user_edit(request, user_id):
    """
    View to edit a user
    """
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('admin_users')
    else:
        form = CustomUserChangeForm(instance=user_obj)
    
    return render(request, 'saas/user_edit.html', {
        'form': form,
        'user_obj': user_obj
    })


@login_required
def user_delete(request, user_id):
    """
    View to delete a user
    """
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('admin_users')
    
    return render(request, 'saas/user_delete.html', {
        'user_obj': user_obj
    })


def roles_list(request):
    """
    View to list all roles
    """
    if not request.user.is_authenticated:
        return redirect('auth:login')
    
    roles = Role.objects.prefetch_related('users').all()
    return render(request, 'base.html', {'users': CustomUser.objects.select_related('role').all(), 'roles': roles})
