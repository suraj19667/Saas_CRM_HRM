# Import all models for easy access
from .user import CustomUser
from .role import Role
from .permission import Permission
from .rolepermission import RolePermission
from .activity import Activity
from .billing import Billing
from .media import Media
from .notification import Notification
from .subscription import Subscription, SubscriptionPlan
from .tenant import Tenant, TenantSetting
from .plan import Plan, OneTimePlan, SubscriptionBillingPlan, CustomEnterprisePlan
from .company_subscription import CompanySubscription
from .payment_transaction import PaymentTransaction
from .module import Module
from .feature import Feature
from .planfeature import PlanFeature
from .addon import Addon
from .invoice import Invoice

# OTP Verification model
from django.db import models
from django.utils import timezone
import random
import string


class OTPVerification(models.Model):
    """OTP verification for secure authentication"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='otp_codes'
    )
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'otp_verification'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"OTP for {self.user.username}: {self.otp}"


__all__ = [
    'CustomUser',
    'Role',
    'Permission',
    'RolePermission',
    'Activity',
    'Billing',
    'Media',
    'Notification',
    'OTPVerification',
    'Subscription',
    'SubscriptionPlan',
    'Tenant',
    'Plan',
    'CompanySubscription',
    'PaymentTransaction',
    'Module',
    'Feature',
    'PlanFeature',
    'Addon',
    'Invoice',
]
