# Data migration to populate initial features

from django.db import migrations


def populate_features(apps, schema_editor):
    Feature = apps.get_model('saas', 'Feature')
    
    # Define common SaaS features based on the project structure
    features = [
        {
            'name': 'User Management',
            'key': 'user_management',
            'description': 'Ability to create, edit, and manage users within the organization'
        },
        {
            'name': 'Role Management',
            'key': 'role_management', 
            'description': 'Create and assign roles with different permission levels'
        },
        {
            'name': 'Permission Management',
            'key': 'permission_management',
            'description': 'Fine-grained control over user permissions and access rights'
        },
        {
            'name': 'CRM Module',
            'key': 'crm_module',
            'description': 'Customer Relationship Management functionality'
        },
        {
            'name': 'HRM Module', 
            'key': 'hrm_module',
            'description': 'Human Resource Management functionality'
        },
        {
            'name': 'Dashboard Analytics',
            'key': 'dashboard_analytics',
            'description': 'Advanced dashboard with analytics and reporting'
        },
        {
            'name': 'File Storage',
            'key': 'file_storage',
            'description': 'File upload and storage capabilities'
        },
        {
            'name': 'API Access',
            'key': 'api_access',
            'description': 'REST API access for third-party integrations'
        },
        {
            'name': 'Multi-tenant Support',
            'key': 'multi_tenant',
            'description': 'Support for multiple isolated tenant environments'
        },
        {
            'name': 'Billing Management',
            'key': 'billing_management',
            'description': 'Subscription billing and payment processing'
        },
        {
            'name': 'Notification System',
            'key': 'notification_system',
            'description': 'Email and in-app notification capabilities'
        },
        {
            'name': 'Activity Logging',
            'key': 'activity_logging',
            'description': 'Track and log user activities and system events'
        }
    ]
    
    for feature_data in features:
        Feature.objects.create(**feature_data)


def reverse_populate_features(apps, schema_editor):
    Feature = apps.get_model('saas', 'Feature')
    Feature.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saas', '0005_add_feature_module_planfeature_models'),
    ]

    operations = [
        migrations.RunPython(
            populate_features, 
            reverse_populate_features
        ),
    ]