"""
Forms for add-on management.
"""

from django import forms
from ..models import Addon


class AddonForm(forms.ModelForm):
    """Form for creating and updating add-ons"""
    
    class Meta:
        model = Addon
        fields = ['name', 'code', 'description', 'price_per_unit', 'unit_name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Add-on name (e.g., Additional Users, Extra Storage)',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unique code (e.g., extra_users, extra_storage)',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Detailed description of the add-on',
                'rows': 4
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price per unit',
                'step': '0.01',
                'required': True
            }),
            'unit_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit name (e.g., user, GB, project)',
                'value': 'unit'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Add-on Name',
            'code': 'Code',
            'description': 'Description',
            'price_per_unit': 'Price Per Unit',
            'unit_name': 'Unit Name',
            'is_active': 'Active'
        }
    
    def clean_code(self):
        """Validate that code is unique (except for current instance)"""
        code = self.cleaned_data.get('code')
        if code:
            # Check if code is unique, excluding current instance
            queryset = Addon.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('An add-on with this code already exists.')
        return code
    
    def clean_price_per_unit(self):
        """Validate price is positive"""
        price = self.cleaned_data.get('price_per_unit')
        if price is not None and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price
