from django.db import models


class Permission(models.Model):
    """
    Permission model for granular access control.
    
    Features:
    - name: Human-readable permission name
    - codename: Unique code for programmatic checks
    - description: Detailed description of the permission
    - module: Category/module the permission belongs to (e.g., 'users', 'roles', 'billing')
    - created_at: Timestamp when permission was created
    """
    
    # Permission modules/categories
    MODULE_CHOICES = [
        ('dashboard', 'Dashboard'),
        ('users', 'User Management'),
        ('roles', 'Role Management'),
        ('permissions', 'Permission Management'),
        ('billing', 'Billing & Subscriptions'),
        ('tenants', 'Tenant Management'),
        ('crm', 'CRM'),
        ('reports', 'Reports'),
        ('settings', 'Settings'),
        ('system', 'System'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='permissions',
        null=True,  # Made nullable to avoid migration issues
        blank=True
    )
    module = models.CharField(
        max_length=50, 
        choices=MODULE_CHOICES,
        default='general'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'permissions'
        ordering = ['module', 'name']
        unique_together = ('codename', 'module')
    
    def __str__(self):
        return f"{self.name} ({self.codename})"
    
    def __repr__(self):
        return f"<Permission: {self.codename}>"
