from django.db import models
from django.utils import timezone


class Plan(models.Model):
    """Subscription plan model"""
    PLAN_TYPE_CHOICES = [
        ('one_time', 'One Time'),
        ('subscription', 'Subscription'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.IntegerField()
    max_storage_mb = models.IntegerField()
    max_projects = models.IntegerField()
    status = models.BooleanField(default=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='subscription')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans'
        ordering = ['price_monthly']
    
    def __str__(self):
        return self.name


class OneTimePlan(models.Model):
    """One-time purchase plans for enterprise clients"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    created_date = models.DateTimeField(auto_now_add=True)
    license_name = models.CharField(max_length=100)
    one_time_price = models.DecimalField(max_digits=15, decimal_places=2)
    employee_limit = models.IntegerField()
    admin_limit = models.IntegerField()
    support_duration = models.IntegerField(help_text="Support duration in months")
    upgrade_eligible = models.BooleanField(default=True)
    customers = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'one_time_plans'
        ordering = ['-created_date']
        verbose_name = 'One Time Plan'
        verbose_name_plural = 'One Time Plans'
    
    def __str__(self):
        return f"{self.license_name} - ₹{self.one_time_price}"


class SubscriptionBillingPlan(models.Model):
    """Subscription plans with recurring billing"""
    BILLING_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    ADDON_CATEGORY_CHOICES = [
        ('users', 'Users'),
        ('feature', 'Feature'),
        ('storage', 'Storage'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    created_date = models.DateTimeField(auto_now_add=True)
    company_name = models.CharField(max_length=150)
    company_email = models.EmailField()
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES)
    add_on_category = models.CharField(max_length=50, choices=ADDON_CATEGORY_CHOICES)
    quantity = models.IntegerField()
    max_quantity = models.IntegerField()
    monthly_price = models.DecimalField(max_digits=15, decimal_places=2)
    subscription_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_billing_plans'
        ordering = ['-created_date']
        verbose_name = 'Subscription Billing Plan'
        verbose_name_plural = 'Subscription Billing Plans'
    
    def __str__(self):
        return f"{self.company_name} - {self.billing_type}"


class CustomEnterprisePlan(models.Model):
    """Custom enterprise plans with negotiated terms"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    created_date = models.DateTimeField(auto_now_add=True)
    company_name = models.CharField(max_length=150)
    company_email = models.EmailField()
    plan_name = models.CharField(max_length=150)
    employee_limit = models.IntegerField()
    contract_duration = models.IntegerField(help_text="Contract duration in months")
    monthly_price = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'custom_enterprise_plans'
        ordering = ['-created_date']
        verbose_name = 'Custom Enterprise Plan'
        verbose_name_plural = 'Custom Enterprise Plans'
    
    def __str__(self):
        return f"{self.plan_name} - {self.company_name}"

