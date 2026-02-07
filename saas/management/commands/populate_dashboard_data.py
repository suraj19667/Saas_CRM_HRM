"""
Management command to populate sample data for StaffGrid Dashboard testing

This command creates:
- Sample revenue data for the past 12 months
- Sample tenants/companies
- Sample plans
- Sample subscriptions

Usage:
    python manage.py populate_dashboard_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random

from saas.models import Revenue, Tenant, Plan, Subscription, CustomUser


class Command(BaseCommand):
    help = 'Populate sample data for StaffGrid Dashboard'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting StaffGrid Dashboard data population...'))
        
        # Create Plans
        self.create_plans()
        
        # Create Revenue Data
        self.create_revenue_data()
        
        # Create Tenants
        self.create_tenants()
        
        # Create Subscriptions
        self.create_subscriptions()
        
        self.stdout.write(self.style.SUCCESS('✅ Dashboard data populated successfully!'))
        self.stdout.write(self.style.SUCCESS('📊 You can now access the StaffGrid Dashboard'))
        self.stdout.write(self.style.WARNING('💡 Access: /staffgrid/'))

    def create_plans(self):
        """Create subscription plans if they don't exist"""
        plans_data = [
            {
                'name': 'Trial',
                'description': 'Trial plan for testing',
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'max_users': 5,
                'max_storage_mb': 1000,
                'max_projects': 3,
                'status': True,
            },
            {
                'name': 'Starter',
                'description': 'Perfect for small teams',
                'price_monthly': Decimal('29.99'),
                'price_yearly': Decimal('299.99'),
                'max_users': 10,
                'max_storage_mb': 5000,
                'max_projects': 10,
                'status': True,
            },
            {
                'name': 'Professional',
                'description': 'For growing businesses',
                'price_monthly': Decimal('79.99'),
                'price_yearly': Decimal('799.99'),
                'max_users': 50,
                'max_storage_mb': 25000,
                'max_projects': 50,
                'status': True,
            },
            {
                'name': 'Enterprise',
                'description': 'For large organizations',
                'price_monthly': Decimal('199.99'),
                'price_yearly': Decimal('1999.99'),
                'max_users': 500,
                'max_storage_mb': 100000,
                'max_projects': 500,
                'status': True,
            },
        ]
        
        created_count = 0
        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created plan: {plan.name}')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Plans: {created_count} new, {len(plans_data) - created_count} existing'))

    def create_revenue_data(self):
        """Create monthly revenue data for the past 12 months"""
        current_date = datetime.now()
        created_count = 0
        
        for i in range(12):
            # Calculate month and year
            month_date = current_date - timedelta(days=30 * i)
            month = month_date.month
            year = month_date.year
            
            # Generate random revenue between 5000 and 15000
            base_amount = Decimal(str(random.uniform(5000, 15000)))
            amount = base_amount.quantize(Decimal('0.01'))
            
            # Create or update revenue record
            revenue, created = Revenue.objects.get_or_create(
                month=month,
                year=year,
                defaults={
                    'amount': amount,
                    'description': f'Monthly revenue for {month_date.strftime("%B %Y")}'
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created revenue: {revenue.get_month_display()} {year} - ${amount}')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Revenue: {created_count} new records'))

    def create_tenants(self):
        """Create sample tenant companies"""
        tenants_data = [
            {'name': 'Tech Innovations Inc', 'is_flagged': False, 'status': 'active'},
            {'name': 'Global Solutions LLC', 'is_flagged': False, 'status': 'active'},
            {'name': 'Digital Wave Corp', 'is_flagged': True, 'status': 'active'},
            {'name': 'Cloud Systems Ltd', 'is_flagged': False, 'status': 'active'},
            {'name': 'Data Analytics Pro', 'is_flagged': False, 'status': 'active'},
            {'name': 'Smart Business Co', 'is_flagged': False, 'status': 'inactive'},
            {'name': 'Enterprise Hub', 'is_flagged': True, 'status': 'active'},
            {'name': 'Startup Accelerator', 'is_flagged': False, 'status': 'active'},
        ]
        
        created_count = 0
        for tenant_data in tenants_data:
            tenant, created = Tenant.objects.get_or_create(
                name=tenant_data['name'],
                defaults={
                    'is_flagged': tenant_data['is_flagged'],
                    'status': tenant_data['status'],
                    'contact_email': f"{tenant_data['name'].lower().replace(' ', '.')}@example.com",
                }
            )
            if created:
                created_count += 1
                flag_emoji = '🚩' if tenant.is_flagged else '✓'
                self.stdout.write(f'  {flag_emoji} Created tenant: {tenant.name}')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Tenants: {created_count} new companies'))

    def create_subscriptions(self):
        """Create subscriptions for tenants"""
        tenants = Tenant.objects.all()
        plans = Plan.objects.all()
        
        if not tenants.exists() or not plans.exists():
            self.stdout.write(self.style.WARNING('⚠️  No tenants or plans available for subscriptions'))
            return
        
        created_count = 0
        for tenant in tenants:
            # Randomly assign a plan
            plan = random.choice(plans)
            
            # Check if subscription already exists
            if Subscription.objects.filter(tenant=tenant).exists():
                continue
            
            # Random start date within last 6 months
            days_ago = random.randint(1, 180)
            start_date = timezone.now().date() - timedelta(days=days_ago)
            
            # Determine billing cycle
            billing_cycle = random.choice(['monthly', 'yearly'])
            
            # Calculate amount
            amount = plan.price_monthly if billing_cycle == 'monthly' else plan.price_yearly
            
            # Create subscription
            subscription = Subscription.objects.create(
                tenant=tenant,
                plan=plan,
                start_date=start_date,
                billing_cycle=billing_cycle,
                amount=amount,
                status='active' if tenant.status == 'active' else 'expired'
            )
            
            created_count += 1
            self.stdout.write(f'  ✓ Created subscription: {tenant.name} → {plan.name}')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Subscriptions: {created_count} created'))
