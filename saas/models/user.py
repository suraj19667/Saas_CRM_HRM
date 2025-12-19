from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from ..manager import CustomUserManager


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    
    Features:
    - Email as login identifier
    - Role-based access control
    - Phone and address fields
    - Profile picture support
    - Email verification tracking
    - Custom user manager for email-based authentication
    """
    
    # Core user fields (inherited from AbstractUser):
    # username, first_name, last_name, email, password, groups, user_permissions
    
    email = models.EmailField(unique=True)
    
    role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Custom manager for email-based authentication
    objects = CustomUserManager()
    
    class Meta:
        db_table = 'custom_users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"
    
    def has_permission(self, codename):
        """
        Check if user has a specific permission via their role.
        
        Args:
            codename (str): Permission codename to check
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        if self.is_superuser or self.is_staff:
            return True
        
        if not self.role:
            return False
        
        return self.role.has_permission(codename)
    
    def get_all_permissions(self):
        """
        Get all permissions for the user via their role.
        
        Returns:
            QuerySet: Set of all permission codenamed for this user
        """
        if self.is_superuser or self.is_staff:
            from .permission import Permission
            return Permission.objects.all()
        
        if not self.role:
            return []
        
        return self.role.get_all_permissions()
    
    def get_permission_codenames(self):
        """
        Get list of permission codenamed strings for this user.
        
        Returns:
            list: List of permission codenamed
        """
        if self.is_superuser or self.is_staff:
            from .permission import Permission
            return list(Permission.objects.values_list('codename', flat=True))
        
        if not self.role:
            return []
        
        return self.role.get_permission_codenames()
