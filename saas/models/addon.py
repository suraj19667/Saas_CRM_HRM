from django.db import models


class Addon(models.Model):
    """Add-on services that tenants can purchase in addition to their base plan"""
    name = models.CharField(max_length=255, help_text="Add-on name (e.g., Additional Users, Extra Storage)")
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the add-on (e.g., 'extra_users', 'extra_storage')")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the add-on")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit (e.g., price per user, per GB)")
    unit_name = models.CharField(max_length=50, default='unit', help_text="Name of the unit (e.g., 'user', 'GB', 'project')")
    is_active = models.BooleanField(default=True, help_text="Whether this add-on is available for purchase")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'addons'
        ordering = ['name']
        verbose_name = 'Add-on'
        verbose_name_plural = 'Add-ons'
    
    def __str__(self):
        return f"{self.name} - ₹{self.price_per_unit}/{self.unit_name}"
