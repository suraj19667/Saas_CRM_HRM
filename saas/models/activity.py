from django.db import models


class Activity(models.Model):
    """Activity log model for tracking user actions"""
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action}"
