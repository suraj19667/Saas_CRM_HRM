from django.db import models


class Media(models.Model):
    """Media/File storage model"""
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='user_files/')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'media'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.file_name
