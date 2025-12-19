from django.db import models


class RolePermission(models.Model):
    """
    Many-to-many relationship between Roles and Permissions with audit trail.
    
    Features:
    - role: ForeignKey to Role
    - permission: ForeignKey to Permission
    - granted_by: Optional reference to user who granted the permission
    - granted_at: Timestamp when permission was granted
    - revoked_at: Timestamp when permission was revoked (if applicable)
    """
    
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission = models.ForeignKey(
        'Permission',
        on_delete=models.CASCADE,
        related_name='permission_roles'
    )
    granted_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_permissions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['permission', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.role.name} → {self.permission.codename}"
    
    def __repr__(self):
        return f"<RolePermission: {self.role.name}:{self.permission.codename}>"
