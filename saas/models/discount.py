from django.db import models
from django.utils import timezone


class Discount(models.Model):
    """Discount model for plans and companies"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('flat', 'Flat'),
    ]
    
    SCOPE_CHOICES = [
        ('global', 'Global (Available System-wide)'),
        ('company_specific', 'Company Specific'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]
    
    APPLICABLE_MODEL_CHOICES = [
        ('all_products', 'All Products'),
        ('specific_plan', 'Specific Plan'),
        ('specific_company', 'Specific Company'),
    ]
    
    discount_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, help_text="Internal use description")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage (0-100) or flat amount")
    applicable_model = models.CharField(max_length=50, choices=APPLICABLE_MODEL_CHOICES, default='all_products')
    scope = models.CharField(max_length=50, choices=SCOPE_CHOICES, default='global')
    start_date = models.DateField()
    end_date = models.DateField()
    auto_expire = models.BooleanField(default=True)
    allow_stacking = models.BooleanField(default=False, help_text="Can be combined with other discounts")
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Maximum number of times this discount can be used (null = unlimited)")
    current_usage = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_discounts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'discounts'
        ordering = ['-created_at']
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'
    
    def __str__(self):
        return f"{self.discount_name} - {self.get_discount_type_display()}"
    
    def is_valid(self):
        """Check if discount is currently valid"""
        today = timezone.now().date()
        if self.status != 'active':
            return False
        if self.start_date > today:
            return False
        if self.end_date < today:
            return False
        if self.usage_limit and self.current_usage >= self.usage_limit:
            return False
        return True
    
    def can_use(self):
        """Check if discount can still be used (not at limit)"""
        if not self.is_valid():
            return False
        if self.usage_limit and self.current_usage >= self.usage_limit:
            return False
        return True
    
    def apply_discount(self, amount):
        """Apply discount to an amount and return discounted amount"""
        if not self.is_valid():
            return amount
        
        if self.discount_type == 'percentage':
            discount_amount = (amount * self.discount_value) / 100
        else:  # flat
            discount_amount = self.discount_value
        
        return max(0, amount - discount_amount)






