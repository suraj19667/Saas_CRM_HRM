from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Tenant(models.Model):
    """Multi-tenant organization model"""
    name = models.CharField(max_length=255, help_text="Company Name")
    domain = models.CharField(max_length=255, unique=True, blank=True, help_text="Unique domain for tenant URL (auto-generated from company name)")
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True, help_text="Company Logo")
    contact_email = models.EmailField(blank=True, null=True, help_text="Contact Email Address")
    contact_phone = models.CharField(max_length=15, blank=True, null=True, help_text="Contact Phone Number")
    address = models.TextField(blank=True, null=True, help_text="Company Address")
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='inactive')
    subscription_plan = models.ForeignKey('Plan', on_delete=models.SET_NULL, null=True, blank=True, related_name='tenants')
    allow_email_notifications = models.BooleanField(default=True, help_text="Allow email notifications")
    allow_sms_notifications = models.BooleanField(default=False, help_text="Allow SMS notifications")
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'tenants'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate unique domain if not provided
        if not self.domain:
            base = slugify(self.name)
            domain_candidate = f"{base}.myapp.com"
            suffix = 1
            while Tenant.objects.filter(domain=domain_candidate).exclude(pk=self.pk).exists():
                domain_candidate = f"{base}-{suffix}.myapp.com"
                suffix += 1
            self.domain = domain_candidate
        
        # Auto-generate unique slug if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug_candidate = base_slug
            suffix = 1
            while Tenant.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{get_random_string(5)}"
                suffix += 1
            self.slug = slug_candidate
        
        super().save(*args, **kwargs)
    
    @property
    def is_subscription_active(self):
        if self.status != 'active':
            return False
        if self.subscription_end_date and timezone.now() > self.subscription_end_date:
            return False
        return True


class TenantSetting(models.Model):
    """Tenant-specific settings"""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    date_format = models.CharField(max_length=20, default='Y-m-d')
    time_format = models.CharField(max_length=20, default='H:i:s')
    language = models.CharField(max_length=10, default='en')
    theme_color = models.CharField(max_length=7, default='#007bff')  # Hex color
    
    class Meta:
        db_table = 'tenant_settings'
    
    def __str__(self):
        return f"Settings for {self.tenant.name}"
