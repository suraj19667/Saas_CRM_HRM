"""
Management command to create demo users for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from saas.models import Role, Tenant, Plan, Subscription
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo users for testing (SUPER_ADMIN and Company users)'

    def handle(self, *args, **options):
        """Create demo users"""
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.HTTP_INFO('Creating Demo Users'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
        
        # ==================== 1. SUPER ADMIN ====================
        self.stdout.write(self.style.WARNING('1. Creating SUPER ADMIN...'))
        
        if User.objects.filter(email='admin@saas.com').exists():
            self.stdout.write(self.style.WARNING('   - Super admin already exists'))
            admin_user = User.objects.get(email='admin@saas.com')
        else:
            # Try different usernames if 'admin' exists
            username = 'superadmin'
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'superadmin{counter}'
                counter += 1
            
            admin_user = User.objects.create_superuser(
                username=username,
                email='admin@saas.com',
                password='admin123',
                first_name='Super',
                last_name='Admin'
            )
            self.stdout.write(self.style.SUCCESS('   ✓ Created super admin'))
        
        self.stdout.write(self.style.SUCCESS(f'   Email: admin@saas.com'))
        self.stdout.write(self.style.SUCCESS(f'   Password: admin123'))
        self.stdout.write(self.style.SUCCESS(f'   Dashboard: /saas-admin/dashboard/\n'))
        
        # ==================== 2. TEST COMPANY ====================
        self.stdout.write(self.style.WARNING('2. Creating Test Company...'))
        
        # Create or get tenant
        tenant, created = Tenant.objects.get_or_create(
            name='Test Company Inc',
            defaults={
                'contact_email': 'company@test.com',
                'contact_phone': '1234567890',
                'address': '123 Test Street',
                'status': 'active',
                'domain': 'testcompany',
                'slug': 'test-company'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('   ✓ Created Test Company'))
        else:
            self.stdout.write(self.style.WARNING('   - Test Company already exists'))
        
        # ==================== 3. ROLES ====================
        self.stdout.write(self.style.WARNING('\n3. Setting up Roles...'))
        
        try:
            admin_role = Role.objects.get(name='COMPANY_ADMIN')
            employee_role = Role.objects.get(name='EMPLOYEE')
            self.stdout.write(self.style.SUCCESS('   ✓ Roles found'))
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ✗ Roles not found. Run: python manage.py init_roles'))
            return
        
        # ==================== 4. COMPANY ADMIN ====================
        self.stdout.write(self.style.WARNING('\n4. Creating Company Admin...'))
        
        if User.objects.filter(email='company@test.com').exists():
            self.stdout.write(self.style.WARNING('   - Company admin already exists'))
            company_admin = User.objects.get(email='company@test.com')
        else:
            company_admin = User.objects.create_user(
                username='company_admin',
                email='company@test.com',
                password='admin123',
                first_name='Company',
                last_name='Admin',
                tenant=tenant,
                role=admin_role,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS('   ✓ Created company admin'))
        
        self.stdout.write(self.style.SUCCESS(f'   Email: company@test.com'))
        self.stdout.write(self.style.SUCCESS(f'   Password: admin123'))
        self.stdout.write(self.style.SUCCESS(f'   Role: COMPANY_ADMIN'))
        
        # ==================== 5. EMPLOYEE ====================
        self.stdout.write(self.style.WARNING('\n5. Creating Employee...'))
        
        if User.objects.filter(email='employee@test.com').exists():
            self.stdout.write(self.style.WARNING('   - Employee already exists'))
            employee = User.objects.get(email='employee@test.com')
        else:
            employee = User.objects.create_user(
                username='employee',
                email='employee@test.com',
                password='employee123',
                first_name='Test',
                last_name='Employee',
                tenant=tenant,
                role=employee_role,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS('   ✓ Created employee'))
        
        self.stdout.write(self.style.SUCCESS(f'   Email: employee@test.com'))
        self.stdout.write(self.style.SUCCESS(f'   Password: employee123'))
        self.stdout.write(self.style.SUCCESS(f'   Role: EMPLOYEE'))
        
        # ==================== 6. SUBSCRIPTION (OPTIONAL) ====================
        self.stdout.write(self.style.WARNING('\n6. Checking Subscription...'))
        
        # Check if plan exists
        plan = Plan.objects.filter(status=True).first()
        
        if not plan:
            # Create a basic plan
            plan = Plan.objects.create(
                name='Basic Plan',
                description='Basic plan for testing',
                price_monthly=99.00,
                price_yearly=999.00,
                max_users=10,
                max_storage_mb=5000,
                max_projects=5,
                status=True,
                plan_type='subscription'
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Created plan: {plan.name}'))
        
        # Check if subscription exists
        subscription = Subscription.objects.filter(
            tenant=tenant,
            status='active'
        ).first()
        
        if not subscription:
            # Create subscription with all required fields
            subscription = Subscription.objects.create(
                tenant=tenant,
                plan=plan,
                status='active',
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timedelta(days=365)).date(),
                billing_cycle='monthly',
                amount=plan.price_monthly
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Created subscription: {plan.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'   - Subscription already exists: {subscription.plan.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'   HRM Dashboard: /hrm/overview/'))
        
        # ==================== SUMMARY ====================
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.HTTP_INFO('DEMO USERS CREATED SUCCESSFULLY'))
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write(self.style.SUCCESS('\n📋 Login Credentials:\n'))
        self.stdout.write(self.style.SUCCESS('1. SUPER ADMIN (SaaS Dashboard)'))
        self.stdout.write(self.style.SUCCESS('   Email: admin@saas.com'))
        self.stdout.write(self.style.SUCCESS('   Password: admin123'))
        self.stdout.write(self.style.SUCCESS('   URL: http://127.0.0.1:8000/saas-admin/dashboard/\n'))
        
        self.stdout.write(self.style.SUCCESS('2. COMPANY ADMIN (HRM Dashboard)'))
        self.stdout.write(self.style.SUCCESS('   Email: company@test.com'))
        self.stdout.write(self.style.SUCCESS('   Password: admin123'))
        self.stdout.write(self.style.SUCCESS('   URL: http://127.0.0.1:8000/hrm/overview/\n'))
        
        self.stdout.write(self.style.SUCCESS('3. EMPLOYEE (HRM Dashboard)'))
        self.stdout.write(self.style.SUCCESS('   Email: employee@test.com'))
        self.stdout.write(self.style.SUCCESS('   Password: employee123'))
        self.stdout.write(self.style.SUCCESS('   URL: http://127.0.0.1:8000/hrm/overview/\n'))
        
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
