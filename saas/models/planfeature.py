from django.db import models
from .plan import Plan
from .feature import Feature


class PlanFeature(models.Model):
    """Feature limits and access control for subscription plans"""
    plan = models.ForeignKey(
        Plan, 
        on_delete=models.CASCADE, 
        related_name='plan_features'
    )
    feature = models.ForeignKey(
        Feature, 
        on_delete=models.CASCADE, 
        related_name='plan_features'
    )
    feature_limit = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Maximum limit for this feature. NULL means unlimited."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plan_features'
        unique_together = ['plan', 'feature']
        ordering = ['plan', 'feature']
    
    def __str__(self):
        limit_text = f"(Limit: {self.feature_limit})" if self.feature_limit else "(Unlimited)"
        return f"{self.plan.name} - {self.feature.name} {limit_text}"