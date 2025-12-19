from django.db import models


class Billing(models.Model):
    """Billing information model"""
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='billing')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billings'
    
    def __str__(self):
        return f"Billing for {self.user.username}"
