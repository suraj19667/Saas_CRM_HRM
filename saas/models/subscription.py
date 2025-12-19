from django.db import models
from datetime import date, timedelta


class Subscription(models.Model):
    """Tenant subscription model"""
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='billing_subscriptions')
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='billing_subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    billing_cycle = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate end_date if not set
        if not self.end_date and self.start_date:
            if self.billing_cycle == 'monthly':
                self.end_date = self.start_date + timedelta(days=30)
            elif self.billing_cycle == 'yearly':
                self.end_date = self.start_date + timedelta(days=365)
        super().save(*args, **kwargs)


class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ("Basic", "Basic"),
        ("Standard", "Standard"),
        ("Premium", "Premium"),
    ]
    name = models.CharField(max_length=50, choices=PLAN_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()  # monthly=30, quarterly=90, yearly=365
    features = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
