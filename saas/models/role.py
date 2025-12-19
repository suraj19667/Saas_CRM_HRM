from django.db import models


class Role(models.Model):
    """
    Role model for grouping permissions and assigning to users.
    
    Features:
    - name: Unique role name (e.g., 'Admin', 'Editor', 'Viewer')
    - description: Detailed description of the role
    - is_system: Whether this is a system role (cannot be deleted)
    - permissions: Many-to-many relationship with permissions via RolePermission
    - created_at/updated_at: Audit timestamps
    """
    
    # Predefined system roles
    ADMIN = 'admin'
    EDITOR = 'editor'
    VIEWER = 'viewer'
    GUEST = 'guest'
    
    SYSTEM_ROLES = [ADMIN, EDITOR, VIEWER, GUEST]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='roles',
        null=True,  # Made nullable to avoid migration issues
        blank=True
    )
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"<Role: {self.name}>"
    
    @property
    def permission_count(self):
        """Get count of permissions assigned to this role."""
        return self.role_permissions.filter(
            permission__is_active=True
        ).count()
    
    @property
    def user_count(self):
        """Get count of users assigned to this role."""
        return self.users.filter(is_active=True).count()
    
    def has_permission(self, codename):
        """
        Check if role has a specific permission.
        
        Args:
            codename (str): Permission codename to check
        
        Returns:
            bool: True if role has permission, False otherwise
        """
        return self.role_permissions.filter(
            permission__codename=codename,
            permission__is_active=True
        ).exists()
    
    def get_all_permissions(self):
        """
        Get all active permissions assigned to this role.
        
        Returns:
            QuerySet: All Permission objects for this role
        """
        return self.role_permissions.filter(
            permission__is_active=True
        ).select_related('permission').values_list('permission', flat=True)
    
    def get_permission_codenames(self):
        """
        Get list of all permission codenamed for this role.
        
        Returns:
            list: List of permission codenamed
        """
        return list(
            self.role_permissions.filter(
                permission__is_active=True
            ).select_related('permission').values_list(
                'permission__codename', flat=True
            )
        )
    
    def get_permissions_by_module(self):
        """
        Get permissions grouped by module.
        
        Returns:
            dict: Dictionary with module as key and permissions as value
        """
        permissions = self.role_permissions.filter(
            permission__is_active=True
        ).select_related('permission').order_by(
            'permission__module', 'permission__name'
        )
        
        result = {}
        for role_perm in permissions:
            module = role_perm.permission.module
            if module not in result:
                result[module] = []
            result[module].append(role_perm.permission)
        
        return result
    
    def add_permission(self, permission):
        """
        Add a permission to this role.
        
        Args:
            permission (Permission): Permission object to add
        
        Returns:
            bool: True if permission was added, False if already exists
        """
        from .permission import RolePermission
        obj, created = RolePermission.objects.get_or_create(
            role=self,
            permission=permission
        )
        return created
    
    def remove_permission(self, permission):
        """
        Remove a permission from this role.
        
        Args:
            permission (Permission): Permission object to remove
        
        Returns:
            bool: True if permission was removed, False if didn't exist
        """
        from .permission import RolePermission
        deleted_count, _ = RolePermission.objects.filter(
            role=self,
            permission=permission
        ).delete()
        return deleted_count > 0
