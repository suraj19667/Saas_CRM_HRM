from django.db import models
from django.utils import timezone


class Revenue(models.Model):
    """
    Revenue tracking model for financial analytics and dashboard reporting.
    
    Tracks monthly revenue metrics for business intelligence and reporting.
    Used for dashboard charts and financial analytics.
    """
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Revenue amount in USD"
    )
    month = models.IntegerField(
        help_text="Month number (1-12)"
    )
    year = models.IntegerField(
        help_text="Year (e.g., 2025)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional revenue description or notes"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Record creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    
    class Meta:
        db_table = 'revenue'
        ordering = ['-year', '-month']
        unique_together = ['month', 'year']
        verbose_name = 'Revenue'
        verbose_name_plural = 'Revenues'
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_month_display()} {self.year}: ${self.amount}"
    
    def get_month_display(self):
        """Return the month name"""
        months = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        return months.get(self.month, 'Unknown')
    
    @classmethod
    def get_yearly_total(cls, year):
        """Calculate total revenue for a specific year"""
        return cls.objects.filter(year=year).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @classmethod
    def get_monthly_data(cls, year=None, limit=12):
        """Get monthly revenue data for charts (latest N months)"""
        queryset = cls.objects.all()
        if year:
            queryset = queryset.filter(year=year)
        return queryset.order_by('-year', '-month')[:limit]
