from django.db import models
from django.utils import timezone


class CompanySubscription(models.Model):
    """Subscription for companies/tenants"""
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='company_subscriptions')
    status = models.CharField(max_length=50, default='pending')  # pending, active, expired, cancelled
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_subscriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name}"

    def is_active(self):
        return self.status == 'active' and (self.end_date is None or timezone.now() <= self.end_date)