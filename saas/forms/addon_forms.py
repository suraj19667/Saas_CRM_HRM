from django import forms
from ..models import Addon


class AddonForm(forms.ModelForm):
    """Form for creating and editing add-ons"""
    
    class Meta:
        model = Addon
        fields = ['name', 'code', 'description', 'price_per_unit', 'unit_name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Additional Users',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., extra_users',
                'required': True,
                'pattern': '[a-z_]+',
                'title': 'Only lowercase letters and underscores allowed'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what this add-on provides'
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 50.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'unit_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., user, GB, project',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Add-on Name',
            'code': 'Add-on Code',
            'description': 'Description',
            'price_per_unit': 'Price per Unit (₹)',
            'unit_name': 'Unit Name',
            'is_active': 'Active'
        }
        help_texts = {
            'code': 'Unique identifier (lowercase, underscores only)',
            'price_per_unit': 'Price charged per unit',
            'unit_name': 'What unit is being charged (e.g., user, GB)',
            'is_active': 'Uncheck to hide this add-on from customers'
        }
