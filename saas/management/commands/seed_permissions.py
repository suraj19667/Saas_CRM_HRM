"""
Management command to seed initial permissions and roles into the database.

Usage:
    python manage.py seed_permissions
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from saas.models import Permission, Role, RolePermission, CustomUser


class Command(BaseCommand):
    help = 'Seed initial permissions and default roles'

    def handle(self, *args, **options):
        """Create default permissions and roles"""
        
        # Define permissions by module
        permissions_data = {
            'dashboard': [
                {'name': 'View Dashboard', 'codename': 'view_dashboard', 'description': 'Can view dashboard'},
                {'name': 'View Analytics', 'codename': 'view_analytics', 'description': 'Can view analytics and reports'},
            ],
            'users': [
                {'name': 'View Users', 'codename': 'view_users', 'description': 'Can view user list'},
                {'name': 'Create User', 'codename': 'create_user', 'description': 'Can create new users'},
                {'name': 'Edit User', 'codename': 'edit_user', 'description': 'Can edit user details'},
                {'name': 'Delete User', 'codename': 'delete_user', 'description': 'Can delete users'},
                {'name': 'Manage User Roles', 'codename': 'manage_user_roles', 'description': 'Can assign roles to users'},
            ],
            'roles': [
                {'name': 'View Roles', 'codename': 'view_role', 'description': 'Can view roles'},
                {'name': 'Create Role', 'codename': 'create_role', 'description': 'Can create new roles'},
                {'name': 'Edit Role', 'codename': 'edit_role', 'description': 'Can edit roles'},
                {'name': 'Delete Role', 'codename': 'delete_role', 'description': 'Can delete roles'},
            ],
            'permissions': [
                {'name': 'View Permissions', 'codename': 'view_permission', 'description': 'Can view permissions'},
                {'name': 'Create Permission', 'codename': 'create_permission', 'description': 'Can create new permissions'},
                {'name': 'Edit Permission', 'codename': 'edit_permission', 'description': 'Can edit permissions'},
                {'name': 'Delete Permission', 'codename': 'delete_permission', 'description': 'Can delete permissions'},
            ],
            'billing': [
                {'name': 'View Billing', 'codename': 'view_billing', 'description': 'Can view billing information'},
                {'name': 'Manage Billing', 'codename': 'manage_billing', 'description': 'Can manage billing'},
                {'name': 'View Invoices', 'codename': 'view_invoices', 'description': 'Can view invoices'},
            ],
            'crm': [
                {'name': 'View Leads', 'codename': 'view_leads', 'description': 'Can view leads'},
                {'name': 'Add Lead', 'codename': 'add_lead', 'description': 'Can add leads'},
                {'name': 'Update Lead', 'codename': 'update_lead', 'description': 'Can update leads'},
                {'name': 'Delete Lead', 'codename': 'delete_lead', 'description': 'Can delete leads'},
                {'name': 'View Deals', 'codename': 'view_deals', 'description': 'Can view deals'},
                {'name': 'Create Deal', 'codename': 'create_deal', 'description': 'Can create deals'},
                {'name': 'Edit Deal', 'codename': 'edit_deal', 'description': 'Can edit deals'},
                {'name': 'View Contracts', 'codename': 'view_contracts', 'description': 'Can view contracts'},
            ],
            'reports': [
                {'name': 'View Reports', 'codename': 'view_reports', 'description': 'Can view reports'},
                {'name': 'Generate Reports', 'codename': 'generate_reports', 'description': 'Can generate reports'},
                {'name': 'Export Reports', 'codename': 'export_reports', 'description': 'Can export reports'},
            ],
            'settings': [
                {'name': 'View Settings', 'codename': 'view_settings', 'description': 'Can view system settings'},
                {'name': 'Manage Settings', 'codename': 'manage_settings', 'description': 'Can manage system settings'},
            ],
            'system': [
                {'name': 'View Audit Logs', 'codename': 'view_audit_logs', 'description': 'Can view audit logs'},
                {'name': 'Manage System', 'codename': 'manage_system', 'description': 'Can manage system'},
            ],
        }
        
        # Create permissions
        created_permissions = {}
        with transaction.atomic():
            for module, perms in permissions_data.items():
                for perm_data in perms:
                    # Try to get existing permission by codename or name
                    permission = None
                    try:
                        permission = Permission.objects.get(codename=perm_data['codename'])
                    except Permission.DoesNotExist:
                        try:
                            permission = Permission.objects.get(name=perm_data['name'])
                        except Permission.DoesNotExist:
                            pass
                    
                    if permission:
                        # Update existing
                        permission.codename = perm_data['codename']
                        permission.name = perm_data['name']
                        permission.module = module
                        permission.description = perm_data['description']
                        permission.is_active = True
                        permission.save()
                        created = False
                    else:
                        # Create new
                        permission = Permission.objects.create(
                            name=perm_data['name'],
                            codename=perm_data['codename'],
                            module=module,
                            description=perm_data['description'],
                            is_active=True,
                        )
                        created = True
                    
                    created_permissions[perm_data['codename']] = permission
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Created permission: {perm_data["codename"]}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Permission already exists: {perm_data["codename"]}')
                        )

            # Ensure required codenames requested by the task exist
            required_codenames = [
                ('add_lead', 'crm'),      # already created as 'Add Lead'
                ('update_lead', 'crm'),   # already created as 'Update Lead'
                ('view_users', 'users'),  # already created as 'View Users'
            ]

            for codename, module in required_codenames:
                # Only add if not already in map
                if codename not in created_permissions:
                    try:
                        perm = Permission.objects.get(codename=codename)
                        created_permissions[codename] = perm
                    except Permission.DoesNotExist:
                        # Try to find a permission with this name pattern
                        try:
                            perm = Permission.objects.get(codename=codename)
                            created_permissions[codename] = perm
                        except Permission.DoesNotExist:
                            pass
            
            # Create default roles
            roles_data = [
                {
                    'name': 'Admin',
                    'description': 'Full access to all features',
                    'is_system': True,
                    'permissions': list(created_permissions.values()),  # All permissions
                },
                {
                    'name': 'Editor',
                    'description': 'Can create and edit content',
                    'is_system': True,
                    'permissions': [
                        created_permissions.get('view_dashboard'),
                        created_permissions.get('view_users'),
                        created_permissions.get('view_role'),
                        created_permissions.get('view_permission'),
                        created_permissions.get('view_leads'),
                        created_permissions.get('add_lead'),
                        created_permissions.get('update_lead'),
                        created_permissions.get('view_deals'),
                        created_permissions.get('create_deal'),
                        created_permissions.get('edit_deal'),
                        created_permissions.get('view_billing'),
                    ],
                },
                {
                    'name': 'Viewer',
                    'description': 'Can only view content',
                    'is_system': True,
                    'permissions': [
                        created_permissions.get('view_dashboard'),
                        created_permissions.get('view_user'),
                        created_permissions.get('view_role'),
                        created_permissions.get('view_permission'),
                        created_permissions.get('view_leads'),
                        created_permissions.get('view_deals'),
                        created_permissions.get('view_contracts'),
                        created_permissions.get('view_billing'),
                        created_permissions.get('view_analytics'),
                    ],
                },
                {
                    'name': 'Guest',
                    'description': 'Limited access guest account',
                    'is_system': True,
                    'permissions': [
                        created_permissions.get('view_dashboard'),
                    ],
                },
            ]
            
            for role_data in roles_data:
                role, created = Role.objects.get_or_create(
                    name=role_data['name'],
                    defaults={
                        'description': role_data['description'],
                        'is_system': role_data['is_system'],
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created role: {role_data["name"]}')
                    )
                else:
                    # Clear existing permissions
                    RolePermission.objects.filter(role=role).delete()
                    self.stdout.write(
                        self.style.WARNING(f'Role already exists: {role_data["name"]} (permissions refreshed)')
                    )
                
                # Assign permissions to role
                for permission in role_data['permissions']:
                    if permission:
                        RolePermission.objects.get_or_create(
                            role=role,
                            permission=permission
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned {role.role_permissions.count()} permissions to {role_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Successfully seeded permissions and roles!')
        )
        # --- Create task-specific roles and default users ---
        with transaction.atomic():
            # Create/Refresh roles requested in task
            role_map = {}
            # superadmin -> all permissions
            super_role, _ = Role.objects.get_or_create(
                name='superadmin',
                defaults={'description': 'Super Administrator', 'is_system': True, 'is_active': True}
            )
            RolePermission.objects.filter(role=super_role).delete()
            for perm in created_permissions.values():
                RolePermission.objects.get_or_create(role=super_role, permission=perm)
            role_map['superadmin'] = super_role

            # manager -> leads only
            manager_role, _ = Role.objects.get_or_create(
                name='manager',
                defaults={'description': 'Leads Manager', 'is_system': False, 'is_active': True}
            )
            RolePermission.objects.filter(role=manager_role).delete()
            for codename in ['view_leads', 'add_lead', 'update_lead', 'delete_lead']:
                perm = created_permissions.get(codename)
                if perm:
                    RolePermission.objects.get_or_create(role=manager_role, permission=perm)
            role_map['manager'] = manager_role

            # editor -> users edit only (no delete)
            editor_role, _ = Role.objects.get_or_create(
                name='editor',
                defaults={'description': 'Editor (users edit only)', 'is_system': False, 'is_active': True}
            )
            RolePermission.objects.filter(role=editor_role).delete()
            for codename in ['view_users', 'edit_user']:
                perm = created_permissions.get(codename)
                if perm:
                    RolePermission.objects.get_or_create(role=editor_role, permission=perm)
            role_map['editor'] = editor_role

            # Create default users with hashed passwords
            defaults = [
                {'username': 'superadmin', 'password': 'SuperPass123!', 'role': 'superadmin', 'is_superuser': True, 'is_staff': True, 'email': 'superadmin@example.com'},
                {'username': 'manager', 'password': 'ManagerPass123!', 'role': 'manager', 'is_superuser': False, 'is_staff': False, 'email': 'manager@example.com'},
                {'username': 'editor', 'password': 'EditorPass123!', 'role': 'editor', 'is_superuser': False, 'is_staff': False, 'email': 'editor@example.com'},
            ]

            for u in defaults:
                try:
                    user, created = CustomUser.objects.get_or_create(
                        username=u['username'],
                        defaults={'email': u['email']}
                    )
                    if created:
                        user.set_password(u['password'])
                        user.is_active = True
                        user.is_superuser = u.get('is_superuser', False)
                        user.is_staff = u.get('is_staff', False)
                        user.role = role_map.get(u['role'])
                        user.is_verified = True
                        user.save()
                        self.stdout.write(self.style.SUCCESS(f'Created user: {u["username"]}'))
                    else:
                        # ensure password/role updated
                        user.is_superuser = u.get('is_superuser', False)
                        user.is_staff = u.get('is_staff', False)
                        user.role = role_map.get(u['role'])
                        user.set_password(u['password'])
                        user.is_verified = True
                        user.save()
                        self.stdout.write(self.style.WARNING(f'User already exists, updated: {u["username"]}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating user {u["username"]}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n✓ Successfully created task-specific roles and default users!'))
