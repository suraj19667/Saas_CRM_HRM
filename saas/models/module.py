from django.db import models
from .tenant import Tenant


class Module(models.Model):
    """Module access control for tenants"""
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='modules'
    )
    module_name = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'modules'
        unique_together = ['tenant', 'module_name']
        ordering = ['tenant', 'module_name']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.module_name}"