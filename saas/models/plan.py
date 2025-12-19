from django.db import models


class Plan(models.Model):
    """Subscription plan model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.IntegerField()
    max_storage_mb = models.IntegerField()
    max_projects = models.IntegerField()
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans'
        ordering = ['price_monthly']
    
    def __str__(self):
        return self.name

