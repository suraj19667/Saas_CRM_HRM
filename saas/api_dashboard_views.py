"""
StaffGrid Dashboard API Views

Provides REST API endpoints for the admin dashboard with real-time data:
- Dashboard statistics (users, revenue, flagged companies)
- Revenue analytics for charts
- Plan distribution analytics
- Tenant/company listing
- Subscription management

All endpoints require authentication and return JSON responses.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import CustomUser, Tenant, Subscription, Plan, Revenue
from .serializers import (
    DashboardStatsSerializer,
    RevenueSerializer,
    TenantSerializer,
    PlanDistributionSerializer
)
from .api_utils import APIResponse


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_dashboard_stats(request):
    """
    GET /api/dashboard/stats/
    
    Returns comprehensive dashboard statistics including all 8 metrics:
    - total_companies: Total tenant/company count
    - active_subscriptions: Active subscription count
    - monthly_revenue: Current month revenue
    - active_trials: Trial subscriptions count
    - suspended_accounts: Inactive/suspended tenant count
    - conversion_rate: Trial to paid conversion rate
    - total_admin_users: Admin/staff user count
    - churn_risk: Companies at risk of churning
    
    Response:
    {
        "success": true,
        "data": {
            "total_companies": 150,
            "active_subscriptions": 120,
            "monthly_revenue": 45600.50,
            ...
        },
        "status": 200
    }
    
    Authentication: Required
    """
    try:
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # 1. Total Companies
        total_companies = Tenant.objects.count()
        
        # 2. Active Subscriptions
        active_subscriptions = Subscription.objects.filter(status='active').count()
        
        # 3. Monthly Revenue (current month)
        monthly_revenue = Revenue.objects.filter(
            month=current_month,
            year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # 4. Active Trials (subscriptions with Trial plans)
        active_trials = Subscription.objects.filter(
            status='active',
            plan__name__icontains='Trial'
        ).count()
        
        # 5. Suspended Accounts
        suspended_accounts = Tenant.objects.filter(status='inactive').count()
        
        # 6. Trial Conversion Rate (trials converted to paid plans)
        total_trials = Subscription.objects.filter(plan__name__icontains='Trial').count()
        converted_trials = Subscription.objects.filter(
            tenant__in=Tenant.objects.filter(
                billing_subscriptions__plan__name__icontains='Trial'
            ).distinct(),
            status='active'
        ).exclude(plan__name__icontains='Trial').count()
        conversion_rate = round((converted_trials / total_trials * 100) if total_trials > 0 else 0, 1)
        
        # 7. Total Admin Users
        total_admin_users = CustomUser.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        ).count()
        
        # 8. Churn Risk (flagged companies or expiring subscriptions)
        churn_risk = Tenant.objects.filter(is_flagged=True).count()
        
        stats_data = {
            'total_companies': total_companies,
            'active_subscriptions': active_subscriptions,
            'monthly_revenue': float(monthly_revenue),
            'active_trials': active_trials,
            'suspended_accounts': suspended_accounts,
            'conversion_rate': conversion_rate,
            'total_admin_users': total_admin_users,
            'churn_risk': churn_risk,
        }
        
        return JsonResponse({
            'success': True,
            'data': stats_data,
            'status': 200
        }, status=200)
        
    except Exception as e:
        return APIResponse.error(
            f'Failed to fetch dashboard stats: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_dashboard_revenue(request):
    """
    GET /api/dashboard/revenue/
    
    Returns month-wise revenue data for bar chart visualization.
    Supports filtering by year and limiting results.
    
    Query Parameters:
    - year: Filter by specific year (optional)
    - limit: Number of months to return (default: 12)
    
    Response:
    {
        "success": true,
        "data": {
            "labels": ["January 2025", "February 2025", ...],
            "values": [5000, 6500, 7200, ...]
        },
        "status": 200
    }
    
    Authentication: Required
    """
    try:
        # Get query parameters
        year = request.GET.get('year')
        limit = int(request.GET.get('limit', 12))
        
        # Fetch revenue data
        if year:
            revenues = Revenue.objects.filter(year=year).order_by('-month')[:limit]
        else:
            revenues = Revenue.objects.all().order_by('-year', '-month')[:limit]
        
        # Serialize for Chart.js
        chart_data = RevenueSerializer.serialize_chart_data(revenues)
        
        return JsonResponse({
            'success': True,
            'data': chart_data,
            'status': 200
        }, status=200)
        
    except Exception as e:
        return APIResponse.error(
            f'Failed to fetch revenue data: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_dashboard_plan_distribution(request):
    """
    GET /api/dashboard/plan-distribution/
    
    Returns plan-wise active subscription distribution for donut chart.
    Shows how many active subscriptions exist for each plan.
    
    Response:
    {
        "success": true,
        "data": {
            "labels": ["Enterprise", "Professional", "Starter", "Trial"],
            "values": [25, 45, 80, 15]
        },
        "status": 200
    }
    
    Authentication: Required
    """
    try:
        # Get active subscription count by plan
        plan_distribution = Subscription.objects.filter(
            status='active'
        ).values(
            'plan__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Format data for serializer
        plan_data = [
            {
                'plan_name': item['plan__name'] or 'No Plan',
                'count': item['count']
            }
            for item in plan_distribution
        ]
        
        # Serialize for Chart.js
        chart_data = PlanDistributionSerializer.serialize_chart_data(plan_data)
        
        return JsonResponse({
            'success': True,
            'data': chart_data,
            'status': 200
        }, status=200)
        
    except Exception as e:
        return APIResponse.error(
            f'Failed to fetch plan distribution: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_tenants_list(request):
    """
    GET /api/tenants/
    
    Returns list of all tenants/companies with pagination support.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10)
    - status: Filter by status (active/inactive)
    - flagged: Filter flagged companies (true/false)
    
    Response:
    {
        "success": true,
        "data": [...],
        "pagination": {
            "current_page": 1,
            "total_pages": 5,
            "total_count": 47
        },
        "status": 200
    }
    
    Authentication: Required
    """
    try:
        # Build queryset with optimization
        tenants = Tenant.objects.select_related('subscription_plan').all()
        
        # Apply filters
        status = request.GET.get('status')
        if status:
            tenants = tenants.filter(status=status)
        
        flagged = request.GET.get('flagged')
        if flagged == 'true':
            tenants = tenants.filter(is_flagged=True)
        elif flagged == 'false':
            tenants = tenants.filter(is_flagged=False)
        
        # Order by most recent
        tenants = tenants.order_by('-created_at')
        
        # Simple pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = tenants.count()
        paginated_tenants = tenants[start:end]
        
        # Serialize
        serialized_data = TenantSerializer.serialize_list(paginated_tenants)
        
        return JsonResponse({
            'success': True,
            'data': serialized_data,
            'pagination': {
                'current_page': page,
                'total_pages': (total_count + page_size - 1) // page_size,
                'total_count': total_count,
                'page_size': page_size
            },
            'status': 200
        }, status=200)
        
    except Exception as e:
        return APIResponse.error(
            f'Failed to fetch tenants: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_plans_list(request):
    """
    GET /api/plans/
    
    Returns list of all subscription plans.
    
    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "Enterprise",
                "price_monthly": 199.99,
                "price_yearly": 1999.99,
                ...
            }
        ],
        "status": 200
    }
    
    Authentication: Required
    """
    try:
        plans = Plan.objects.filter(status=True).order_by('price_monthly')
        
        serialized_data = [
            {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'price_monthly': float(plan.price_monthly),
                'price_yearly': float(plan.price_yearly),
                'max_users': plan.max_users,
                'max_storage_mb': plan.max_storage_mb,
                'max_projects': plan.max_projects,
                'status': plan.status,
                'plan_type': plan.plan_type,
            }
            for plan in plans
        ]
        
        return JsonResponse({
            'success': True,
            'data': serialized_data,
            'status': 200
        }, status=200)
        
    except Exception as e:
        return APIResponse.error(
            f'Failed to fetch plans: {str(e)}',
            status_code=500
        )


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def api_subscriptions_list(request):
    """
    GET /api/subscriptions/
    
    Returns list of all subscriptions with tenant and plan details.
    
    Query Parameters:
    - status: Filter by status (active/expired/cancelled)
    - tenant_id: Filter by specific tenant
    
    Response:
    {
        "success": true,
        "data": [...],
        "status": 200
    }
    
    Authentication: Required
    """
    try:
        # Build optimized queryset
        subscriptions = Subscription.objects.select_related(
            'tenant', 'plan'
        ).all()
        
        # Apply filters
        status = request.GET.get('status')
        if status:
            subscriptions = subscriptions.filter(status=status)
        
        tenant_id = request.GET.get('tenant_id')
        if tenant_id:
            subscriptions = subscriptions.filter(tenant_id=tenant_id)
        
        # Order by most recent
        subscriptions = subscriptions.order_by('-created_at')[:100]
        
        # Serialize
        serialized_data = [
            {
                'id': sub.id,
                'tenant_id': sub.tenant.id,
                'tenant_name': sub.tenant.name,
                'plan_id': sub.plan.id,
                'plan_name': sub.plan.name,
                'start_date': sub.start_date.isoformat() if sub.start_date else None,
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
                'billing_cycle': sub.billing_cycle,
                'amount': float(sub.amount),
                'status': sub.status,
                'created_at': sub.created_at.isoformat() if sub.created_at else None,
            }
            for sub in subscriptions
        ]
        
        return JsonResponse({
            'success': True,
            'data': serialized_data,
            'status': 200
        }, status=200)
        
    except Exception as e:
        return APIResponse.error(
            f'Failed to fetch subscriptions: {str(e)}',
            status_code=500
        )
