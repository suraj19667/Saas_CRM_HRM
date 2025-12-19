from django.db import models


class PaymentTransaction(models.Model):
    """Payment transaction records for Razorpay"""
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    billing_cycle = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    status = models.CharField(max_length=50, choices=[
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='created')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.razorpay_order_id} - {self.status}"