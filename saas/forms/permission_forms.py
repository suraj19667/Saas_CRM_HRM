from django import forms
from ..models import Permission, RolePermission


class PermissionForm(forms.ModelForm):
    """Form for creating and editing permissions"""
    
    class Meta:
        model = Permission
        fields = ['name', 'codename', 'description', 'module', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter permission name (e.g., "Create User")'
            }),
            'codename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter codename (e.g., "create_user")'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter permission description',
                'rows': 3
            }),
            'module': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class RolePermissionForm(forms.Form):
    """Form for assigning permissions to a role"""
    
    def __init__(self, role=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = role
        
        # Group permissions by module
        permissions = Permission.objects.filter(is_active=True).order_by('module', 'name')
        
        # Create checkboxes for each permission grouped by module
        modules = {}
        for perm in permissions:
            if perm.module not in modules:
                modules[perm.module] = []
            modules[perm.module].append(perm)
        
        # Create a field for each module with its permissions
        for module, perms in sorted(modules.items()):
            choices = [(perm.id, perm.name) for perm in perms]
            field_name = f'permissions_{module}'
            self.fields[field_name] = forms.MultipleChoiceField(
                choices=choices,
                widget=forms.CheckboxSelectMultiple(attrs={
                    'class': 'form-check-input'
                }),
                required=False,
                label=f"{dict(Permission.MODULE_CHOICES).get(module, module)} Permissions"
            )
    
    def save(self):
        """Save the permissions for the role"""
        if not self.role:
            return
        
        # Clear existing permissions
        RolePermission.objects.filter(role=self.role).delete()
        
        # Add new permissions
        for field_name, field_value in self.cleaned_data.items():
            if field_name.startswith('permissions_'):
                for permission_id in field_value:
                    permission = Permission.objects.get(id=permission_id)
                    RolePermission.objects.create(
                        role=self.role,
                        permission=permission
                    )
