"""
API Serializers for model data validation and response formatting.

Provides:
- SubscriptionPlanSerializer: Serialize/deserialize SubscriptionPlan model
- Dashboard serializers for analytics and reporting
- Input validation for JSON fields
- Custom validation methods
"""

import json
from saas.models.subscription import SubscriptionPlan
from saas.models import Revenue, Tenant, Subscription, CustomUser, Plan


class SubscriptionPlanSerializer:
    """
    Serializer for SubscriptionPlan model.
    
    Handles:
    - Conversion of SubscriptionPlan objects to JSON-serializable dicts
    - Validation of input data before saving
    - JSON field parsing and validation
    """
    @staticmethod
    def serialize(plan):
        """
        Convert a SubscriptionPlan instance to a dictionary.
        Args:
            plan (SubscriptionPlan): Model instance
        Returns:
            dict: Serialized plan data
        """
        return {
            'id': plan.id,
            'name': plan.name,
            'price': float(plan.price),
            'duration_days': plan.duration_days,
            'features': plan.features,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
        }

    @staticmethod
    def serialize_list(plans):
        """
        Convert a queryset or list of SubscriptionPlan objects to list of dicts.
        """
        return [SubscriptionPlanSerializer.serialize(plan) for plan in plans]

    @staticmethod
    def validate_data(data):
        """
        Validate input data for SubscriptionPlan creation/update.
        Returns (is_valid, errors, cleaned_data)
        """
        errors = {}
        cleaned = {}
        # Name
        if 'name' not in data or not data['name']:
            errors['name'] = 'Name is required.'
        elif data['name'] not in dict(SubscriptionPlan.PLAN_CHOICES):
            errors['name'] = f"Plan name must be one of: {', '.join([c[0] for c in SubscriptionPlan.PLAN_CHOICES])}"
        else:
            cleaned['name'] = data['name']
        # Price
        try:
            price = float(data.get('price', 0))
            if price <= 0:
                errors['price'] = 'Price must be greater than 0.'
            else:
                cleaned['price'] = price
        except Exception:
            errors['price'] = 'Invalid price.'
        # Duration
        try:
            duration = int(data.get('duration_days', 0))
            if duration not in [30, 90, 365]:
                errors['duration_days'] = 'Duration must be 30, 90, or 365.'
            else:
                cleaned['duration_days'] = duration
        except Exception:
            errors['duration_days'] = 'Invalid duration.'
        # Features
        features = data.get('features')
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except Exception:
                errors['features'] = 'Features must be a valid JSON array.'
        if not errors and (not isinstance(features, list)):
            errors['features'] = 'Features must be a list.'
        else:
            cleaned['features'] = features
        return (len(errors) == 0, errors, cleaned)

    @staticmethod
    def create_from_data(data):
        """
        Create a SubscriptionPlan from validated data dict.
        """
        plan = SubscriptionPlan(
            name=data['name'],
            price=data['price'],
            duration_days=data['duration_days'],
            features=data['features'],
        )
        plan.save()
        return plan

    @staticmethod
    def update_from_data(plan, data):
        """
        Update an existing SubscriptionPlan from validated data dict.
        """
        plan.name = data['name']
        plan.price = data['price']
        plan.duration_days = data['duration_days']
        plan.features = data['features']


class DashboardStatsSerializer:
    """Serializer for dashboard statistics"""
    
    @staticmethod
    def serialize(stats_data):
        """
        Serialize dashboard stats data
        
        Args:
            stats_data (dict): Dictionary containing dashboard statistics
            
        Returns:
            dict: Formatted statistics for API response
        """
        return {
            'total_users': stats_data.get('total_users', 0),
            'active_users': stats_data.get('active_users', 0),
            'total_revenue': float(stats_data.get('total_revenue', 0)),
            'companies_flagged': stats_data.get('companies_flagged', 0),
        }


class RevenueSerializer:
    """Serializer for Revenue model"""
    
    @staticmethod
    def serialize(revenue):
        """
        Convert a Revenue instance to a dictionary
        
        Args:
            revenue (Revenue): Revenue model instance
            
        Returns:
            dict: Serialized revenue data
        """
        return {
            'id': revenue.id,
            'amount': float(revenue.amount),
            'month': revenue.month,
            'year': revenue.year,
            'month_name': revenue.get_month_display(),
            'description': revenue.description,
            'created_at': revenue.created_at.isoformat() if revenue.created_at else None,
        }
    
    @staticmethod
    def serialize_list(revenues):
        """Convert a queryset or list of Revenue objects to list of dicts"""
        return [RevenueSerializer.serialize(revenue) for revenue in revenues]
    
    @staticmethod
    def serialize_chart_data(revenues):
        """
        Format revenue data specifically for Chart.js consumption
        
        Args:
            revenues: QuerySet or list of Revenue objects
            
        Returns:
            dict: Chart.js formatted data with labels and values
        """
        labels = []
        values = []
        
        for revenue in revenues:
            labels.append(f"{revenue.get_month_display()} {revenue.year}")
            values.append(float(revenue.amount))
        
        return {
            'labels': labels,
            'values': values,
        }


class TenantSerializer:
    """Serializer for Tenant/Company model"""
    
    @staticmethod
    def serialize(tenant):
        """
        Convert a Tenant instance to a dictionary
        
        Args:
            tenant (Tenant): Tenant model instance
            
        Returns:
            dict: Serialized tenant data
        """
        return {
            'id': tenant.id,
            'name': tenant.name,
            'domain': tenant.domain,
            'contact_email': tenant.contact_email,
            'contact_phone': tenant.contact_phone,
            'status': tenant.status,
            'is_flagged': tenant.is_flagged,
            'subscription_plan': tenant.subscription_plan.name if tenant.subscription_plan else None,
            'subscription_start_date': tenant.subscription_start_date.isoformat() if tenant.subscription_start_date else None,
            'subscription_end_date': tenant.subscription_end_date.isoformat() if tenant.subscription_end_date else None,
            'is_subscription_active': tenant.is_subscription_active,
            'created_at': tenant.created_at.isoformat() if tenant.created_at else None,
        }
    
    @staticmethod
    def serialize_list(tenants):
        """Convert a queryset or list of Tenant objects to list of dicts"""
        return [TenantSerializer.serialize(tenant) for tenant in tenants]


class PlanDistributionSerializer:
    """Serializer for plan distribution analytics"""
    
    @staticmethod
    def serialize_chart_data(plan_data):
        """
        Format plan distribution data for Chart.js donut/pie charts
        
        Args:
            plan_data: List of dicts with 'plan_name' and 'count' keys
            
        Returns:
            dict: Chart.js formatted data
        """
        labels = []
        values = []
        
        for item in plan_data:
            labels.append(item['plan_name'])
            values.append(item['count'])
        
        return {
            'labels': labels,
            'values': values,
        }


