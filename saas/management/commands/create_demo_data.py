"""
Management command to create demo data for HRM SaaS

Creates:
- Demo Company (Tenant)
- HRM Admin User
- Business Pro Plan
- Active Subscription
- Usage data (employees, admins, storage, modules)

Usage:
    python manage.py create_demo_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from saas.models import (
    Tenant, Plan, Subscription, CustomUser,
    Module, Feature, PlanFeature, Role
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo data for HRM SaaS Dashboard'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating HRM Demo Data...'))
        
        # Step 1: Create Business Pro Plan
        plan = self.create_business_pro_plan()
        
        # Step 2: Create Demo Company
        tenant = self.create_demo_company()
        
        # Step 3: Create HRM Admin User
        admin_user = self.create_hrm_admin(tenant)
        
        # Step 4: Create Active Subscription
        subscription = self.create_active_subscription(tenant, plan)
        
        # Step 5: Create Modules and Features
        self.create_modules_and_features(plan, tenant)
        
        # Step 6: Create Demo Employees (for usage stats)
        self.create_demo_employees(tenant)
        
        self.stdout.write(self.style.SUCCESS('✅ Demo data created successfully!'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('📋 Demo Account Details:'))
        self.stdout.write(self.style.SUCCESS(f'   Company: {tenant.name}'))
        self.stdout.write(self.style.SUCCESS(f'   Email: {admin_user.email}'))
        self.stdout.write(self.style.SUCCESS(f'   Password: demo123'))
        self.stdout.write(self.style.SUCCESS(f'   Plan: {plan.name}'))
        self.stdout.write(self.style.SUCCESS(f'   Status: {subscription.status}'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('🌐 Access HRM Dashboard:'))
        self.stdout.write(self.style.SUCCESS('   URL: http://localhost:8000/hrm/overview/'))

    def create_business_pro_plan(self):
        """Create Business Pro Plan"""
        plan, created = Plan.objects.get_or_create(
            name='Business Pro',
            defaults={
                'description': 'Perfect for growing businesses',
                'price_monthly': Decimal('12999.00'),
                'price_yearly': Decimal('129999.00'),
                'max_users': 200,
                'max_storage_mb': 10240,  # 10 GB
                'max_projects': 100,
                'status': True,
                'plan_type': 'subscription',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created plan: {plan.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'✓ Plan already exists: {plan.name}'))
        
        return plan

    def create_demo_company(self):
        """Create Demo Company (Tenant)"""
        tenant, created = Tenant.objects.get_or_create(
            domain='democompany.mini-saas.local',
            defaults={
                'name': 'Demo Company Ltd.',
                'address': '123 Business Street, Tech City, TC 12345',
                'contact_phone': '+91-9876543210',
                'contact_email': 'admin@democompany.com',
                'status': 'active',
                'slug': 'democompany',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created company: {tenant.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'✓ Company already exists: {tenant.name}'))
        
        return tenant

    def create_hrm_admin(self, tenant):
        """Create HRM Admin User"""
        # First, create or get admin role (check if it exists globally first)
        admin_role = Role.objects.filter(name='Admin').first()
        if not admin_role:
            admin_role = Role.objects.create(
                name='Admin',
                tenant=tenant,
                description='Administrator role with full access',
            )
        
        admin_user, created = CustomUser.objects.get_or_create(
            email='admin@democompany.com',
            defaults={
                'username': 'hrm_admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'is_verified': True,  # Mark as verified so user can login
                'tenant': tenant,
                'role': admin_role,
            }
        )
        
        if created:
            admin_user.set_password('demo123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {admin_user.email}'))
        else:
            # Update password, tenant and verification status
            admin_user.set_password('demo123')
            admin_user.tenant = tenant
            admin_user.role = admin_role
            admin_user.is_verified = True  # Ensure verified
            admin_user.save()
            self.stdout.write(self.style.WARNING(f'✓ Admin user already exists: {admin_user.email}'))
        
        return admin_user

    def create_active_subscription(self, tenant, plan):
        """Create Active Subscription"""
        # Delete any existing subscriptions for this tenant
        Subscription.objects.filter(tenant=tenant).delete()
        
        start_date = date.today() - timedelta(days=16)  # Started 16 days ago (Jan 15, 2025)
        end_date = date.today() + timedelta(days=14)     # Renews in 14 days (Feb 14, 2025)
        
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            billing_cycle='monthly',
            amount=plan.price_monthly,
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created active subscription'))
        self.stdout.write(self.style.SUCCESS(f'   Purchase Date: {subscription.start_date}'))
        self.stdout.write(self.style.SUCCESS(f'   Next Renewal: {subscription.end_date}'))
        
        return subscription

    def create_modules_and_features(self, plan, tenant):
        """Create Modules and Features for the tenant"""
        modules_data = [
            'Employee Management',
            'Payroll Processing',
            'Attendance & Leave',
            'Performance Reviews',
            'Recruitment',
            'Training & LMS',
        ]
        
        created_count = 0
        for module_name in modules_data:
            module, created = Module.objects.get_or_create(
                tenant=tenant,
                module_name=module_name,
                defaults={
                    'is_enabled': True,
                }
            )
            if created:
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {created_count} modules'))
        else:
            self.stdout.write(self.style.WARNING(f'✓ Modules already exist'))

    def create_demo_employees(self, tenant):
        """Create demo employees for usage statistics"""
        # Get or create employee role (check if exists globally first)
        employee_role = Role.objects.filter(name='Employee').first()
        if not employee_role:
            employee_role = Role.objects.create(
                name='Employee',
                tenant=tenant,
                description='Standard employee role',
            )
        
        admin_role = Role.objects.filter(name='Admin').first()
        if not admin_role:
            admin_role = Role.objects.create(
                name='Admin',
                tenant=tenant,
                description='Administrator role',
            )
        
        # Create 187 employees (to match the 187/200 usage shown in the image)
        employee_count = CustomUser.objects.filter(tenant=tenant, role=employee_role).count()
        
        if employee_count >= 187:
            self.stdout.write(self.style.WARNING(f'✓ Already have {employee_count} employees'))
        else:
            employees_to_create = 187 - employee_count
            
            self.stdout.write(self.style.SUCCESS(f'Creating {employees_to_create} demo employees...'))
            
            for i in range(employees_to_create):
                email = f'employee{i+1}@democompany.com'
                
                # Check if user already exists
                if not CustomUser.objects.filter(email=email).exists():
                    CustomUser.objects.create(
                        email=email,
                        username=f'employee{i+1}',
                        first_name=f'Employee',
                        last_name=f'{i+1}',
                        is_staff=False,
                        is_superuser=False,
                        is_active=True,
                        tenant=tenant,
                        role=employee_role,
                        password='pbkdf2_sha256$260000$dummy$dummy',  # Dummy password
                    )
        
        # Create 4 admin users (to match 4/5 admins shown)
        admin_count = CustomUser.objects.filter(tenant=tenant, role=admin_role).count()
        admins_to_create = max(0, 4 - admin_count)
        
        for i in range(admins_to_create):
            email = f'admin{i+2}@democompany.com'
            
            if not CustomUser.objects.filter(email=email).exists():
                CustomUser.objects.create(
                    email=email,
                    username=f'admin{i+2}',
                    first_name=f'Admin',
                    last_name=f'{i+2}',
                    is_staff=False,
                    is_superuser=False,
                    is_active=True,
                    tenant=tenant,
                    role=admin_role,
                    password='pbkdf2_sha256$260000$dummy$dummy',
                )
        
        total_employees = CustomUser.objects.filter(tenant=tenant, role=employee_role).count()
        total_admins = CustomUser.objects.filter(tenant=tenant, role=admin_role).count()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Total Employees: {total_employees}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total Admins: {total_admins}'))
