from django import forms
from saas.models.discount import Discount


class DiscountForm(forms.ModelForm):
    """Form for creating and editing discounts"""
    
    class Meta:
        model = Discount
        fields = [
            'discount_name',
            'description',
            'discount_type',
            'discount_value',
            'applicable_model',
            'scope',
            'start_date',
            'end_date',
            'auto_expire',
            'allow_stacking',
            'usage_limit',
            'status'
        ]
        widgets = {
            'discount_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., New Year 2024 Sale',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal Note about this Discount',
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '14.000',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'applicable_model': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'scope': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'auto_expire': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'allow_stacking': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'usage_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave empty for unlimited',
                'min': '1',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].label_suffix = ""
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        
        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError(
                    'End date must be after start date.'
                )
        
        # Validate percentage discount (0-100)
        if discount_type == 'percentage' and discount_value:
            if discount_value < 0 or discount_value > 100:
                raise forms.ValidationError(
                    'Percentage discount must be between 0 and 100.'
                )
        
        return cleaned_data






