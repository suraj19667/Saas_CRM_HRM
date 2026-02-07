# Views for the new SaaS platform pages

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from ..models import CustomUser, Tenant, Subscription, Plan

def landing_view(request):
    """
    Professional landing page for the SaaS platform
    """
    if request.user.is_authenticated:
        # Redirect authenticated users based on role
        if request.user.is_superuser or request.user.is_staff:
            return redirect('dashboard_overview')  # StaffGrid Dashboard
        else:
            # Regular users go to HRM dashboard
            return redirect('hrm_overview')  # HRM Dashboard
    
    return render(request, 'landing.html')


@login_required(login_url='auth:login')
@never_cache
def dashboard_main_view(request):
    """
    Main dashboard view with stats and analytics
    """
    # Get stats
    total_users = CustomUser.objects.count()
    total_tenants = Tenant.objects.count()
    total_subscriptions = Subscription.objects.filter(status='active').count()
    total_plans = Plan.objects.count()
    
    # Get recent users
    recent_users = CustomUser.objects.select_related('tenant').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_tenants': total_tenants,
        'total_subscriptions': total_subscriptions,
        'total_plans': total_plans,
        'recent_users': recent_users,
    }
    
    return render(request, 'dashboard/main.html', context)


@login_required(login_url='auth:login')
@never_cache
def profile_view(request):
    """
    User profile page
    """
    if request.method == 'POST':
        # Update user profile
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Add phone_number if the field exists
        phone = request.POST.get('phone', '')
        if hasattr(user, 'phone_number'):
            user.phone_number = phone
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'dashboard/profile.html')


@login_required(login_url='auth:login')
@never_cache
def change_password_view(request):
    """
    Change password functionality
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('auth:login')
    
    return redirect('profile')


@login_required(login_url='auth:login')
@never_cache
def settings_view(request):
    """
    Settings page
    """
    if request.method == 'POST':
        # Handle settings update
        messages.success(request, 'Settings updated successfully!')
        return redirect('settings')
    
    return render(request, 'dashboard/settings.html')


@login_required(login_url='auth:login')
@never_cache
def analytics_view(request):
    """
    Analytics page
    """
    context = {}
    return render(request, 'dashboard/analytics.html', context)


def forgot_password_view(request):
    """
    Forgot password page
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        # TODO: Implement password reset email logic
        messages.success(request, 'If an account exists with that email, you will receive password reset instructions.')
        return redirect('auth:login')
    
    return render(request, 'auth/forgot_password.html')
