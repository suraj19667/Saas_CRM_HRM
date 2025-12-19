from django.db import models


class Feature(models.Model):
    """Feature definitions for the system"""
    name = models.CharField(max_length=100, unique=True)
    key = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique key for programmatic access to feature"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'features'
        ordering = ['name']
    
    def __str__(self):
        return self.name