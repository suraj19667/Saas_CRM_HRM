# Data migration to set up plan-feature relationships

from django.db import migrations


def setup_plan_features(apps, schema_editor):
    Plan = apps.get_model('saas', 'Plan')
    Feature = apps.get_model('saas', 'Feature')
    PlanFeature = apps.get_model('saas', 'PlanFeature')
    
    # Get all existing plans and features
    plans = Plan.objects.all()
    features = {f.key: f for f in Feature.objects.all()}
    
    # Define feature limits for different plan types
    plan_feature_mapping = {
        # Basic plan limits (assuming lowest tier)
        'basic': {
            'user_management': 10,  # 10 users max
            'role_management': 3,   # 3 roles max
            'permission_management': 50, # 50 permissions max
            'crm_module': 100,      # 100 contacts max
            'file_storage': 1024,   # 1GB storage
            'dashboard_analytics': 5, # 5 dashboard widgets
            'activity_logging': 1000, # 1000 log entries
            'notification_system': 100, # 100 notifications/month
        },
        # Standard plan limits
        'standard': {
            'user_management': 50,
            'role_management': 10,
            'permission_management': 200,
            'crm_module': 1000,
            'hrm_module': 50,      # Enable HRM for standard+
            'file_storage': 5120,  # 5GB storage
            'dashboard_analytics': 20,
            'activity_logging': 10000,
            'notification_system': 1000,
            'api_access': None,    # Unlimited API access
            'multi_tenant': 1,     # Single tenant
        },
        # Premium plan limits
        'premium': {
            'user_management': None,  # Unlimited users
            'role_management': None,  # Unlimited roles
            'permission_management': None,
            'crm_module': None,
            'hrm_module': None,
            'file_storage': 20480,  # 20GB storage
            'dashboard_analytics': None,
            'activity_logging': None,
            'notification_system': None,
            'api_access': None,
            'multi_tenant': 5,      # Up to 5 tenants
            'billing_management': None,
        },
        # Enterprise plan limits
        'enterprise': {
            'user_management': None,
            'role_management': None,
            'permission_management': None,
            'crm_module': None,
            'hrm_module': None,
            'file_storage': None,   # Unlimited storage
            'dashboard_analytics': None,
            'activity_logging': None,
            'notification_system': None,
            'api_access': None,
            'multi_tenant': None,   # Unlimited tenants
            'billing_management': None,
        }
    }
    
    # Assign features to plans based on plan name patterns
    for plan in plans:
        plan_name_lower = plan.name.lower()
        
        # Determine plan type based on name
        if 'basic' in plan_name_lower or 'starter' in plan_name_lower:
            plan_type = 'basic'
        elif 'standard' in plan_name_lower or 'professional' in plan_name_lower:
            plan_type = 'standard'
        elif 'premium' in plan_name_lower or 'plus' in plan_name_lower:
            plan_type = 'premium'
        elif 'enterprise' in plan_name_lower or 'business' in plan_name_lower:
            plan_type = 'enterprise'
        else:
            # Default to standard for unrecognized plan names
            plan_type = 'standard'
        
        # Get feature mapping for this plan type
        feature_mapping = plan_feature_mapping.get(plan_type, plan_feature_mapping['standard'])
        
        # Create PlanFeature relationships
        for feature_key, limit in feature_mapping.items():
            if feature_key in features:
                PlanFeature.objects.create(
                    plan=plan,
                    feature=features[feature_key],
                    feature_limit=limit
                )


def reverse_setup_plan_features(apps, schema_editor):
    PlanFeature = apps.get_model('saas', 'PlanFeature')
    PlanFeature.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saas', '0006_populate_initial_features'),
    ]

    operations = [
        migrations.RunPython(
            setup_plan_features,
            reverse_setup_plan_features
        ),
    ]