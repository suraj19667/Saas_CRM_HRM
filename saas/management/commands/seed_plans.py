"""
Management command to seed subscription plans into the database.

Usage:
    python manage.py seed_plans
"""

from django.core.management.base import BaseCommand
from saas.models import Plan


class Command(BaseCommand):
    help = 'Seed subscription plans'

    def handle(self, *args, **options):
        """Create default subscription plans"""

        plans_data = [
            {
                'name': 'Basic',
                'description': 'Perfect for small teams getting started',
                'price_monthly': 9.99,
                'price_yearly': 99.99,
                'max_users': 5,
                'max_storage_mb': 1000,
                'max_projects': 10,
                'status': True,
            },
            {
                'name': 'Standard',
                'description': 'Ideal for growing businesses',
                'price_monthly': 19.99,
                'price_yearly': 199.99,
                'max_users': 25,
                'max_storage_mb': 5000,
                'max_projects': 50,
                'status': True,
            },
            {
                'name': 'Premium',
                'description': 'For large organizations with advanced needs',
                'price_monthly': 39.99,
                'price_yearly': 399.99,
                'max_users': 100,
                'max_storage_mb': 25000,
                'max_projects': 200,
                'status': True,
            }
        ]

        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'description': plan_data['description'],
                    'price_monthly': plan_data['price_monthly'],
                    'price_yearly': plan_data['price_yearly'],
                    'max_users': plan_data['max_users'],
                    'max_storage_mb': plan_data['max_storage_mb'],
                    'max_projects': plan_data['max_projects'],
                    'status': plan_data['status'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Plan already exists: {plan.name}')
                )