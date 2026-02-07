"""
Management command to initialize system roles
"""
from django.core.management.base import BaseCommand
from saas.models import Role


class Command(BaseCommand):
    help = 'Initialize system roles for the application'

    def handle(self, *args, **options):
        """Create default system roles"""
        
        roles_data = [
            {
                'name': 'COMPANY_ADMIN',
                'description': 'Company administrator with full access to HRM features',
                'is_system': True,
            },
            {
                'name': 'ADMIN',
                'description': 'Administrator role for company management',
                'is_system': True,
            },
            {
                'name': 'EMPLOYEE',
                'description': 'Regular employee with limited HRM access',
                'is_system': True,
            },
            {
                'name': 'MANAGER',
                'description': 'Manager with team management capabilities',
                'is_system': True,
            },
        ]
        
        created_count = 0
        existing_count = 0
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_system': role_data['is_system'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created role: {role.name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'- Role already exists: {role.name}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Initialization complete! Created: {created_count}, Existing: {existing_count}'
            )
        )
