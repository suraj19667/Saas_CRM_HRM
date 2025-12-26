# Migration to add module-specific features for plan creation form

from django.db import migrations


def add_module_features(apps, schema_editor):
    """Add module-specific features needed for plan management"""
    Feature = apps.get_model('saas', 'Feature')
    
    module_features = [
        {
            'name': 'Employee Management',
            'key': 'employee_management',
            'description': 'Employee management and HR operations'
        },
        {
            'name': 'Attendance Management',
            'key': 'attendance_management',
            'description': 'Employee attendance tracking and management'
        },
        {
            'name': 'Leave Management',
            'key': 'leave_management',
            'description': 'Leave application and approval system'
        },
        {
            'name': 'Payroll Management',
            'key': 'payroll_management',
            'description': 'Payroll processing and salary management'
        },
        {
            'name': 'Expense Management',
            'key': 'expense_management',
            'description': 'Employee expense tracking and reimbursement'
        },
        {
            'name': 'Broadcast Messages',
            'key': 'broadcast_messages',
            'description': 'Send broadcast messages to employees'
        },
        {
            'name': 'Analytics Module',
            'key': 'analytics_module',
            'description': 'Advanced analytics and reporting module'
        },
    ]
    
    for feature_data in module_features:
        Feature.objects.get_or_create(
            key=feature_data['key'],
            defaults={
                'name': feature_data['name'],
                'description': feature_data['description']
            }
        )


def reverse_add_module_features(apps, schema_editor):
    """Remove module-specific features"""
    Feature = apps.get_model('saas', 'Feature')
    Feature.objects.filter(
        key__in=[
            'employee_management',
            'attendance_management', 
            'leave_management',
            'payroll_management',
            'expense_management',
            'broadcast_messages',
            'analytics_module'
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saas', '0015_fix_tenant_settings_schema'),
    ]

    operations = [
        migrations.RunPython(
            add_module_features,
            reverse_add_module_features
        ),
    ]
