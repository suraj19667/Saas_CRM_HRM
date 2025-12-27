from django import forms
from saas.models.plan import Plan, OneTimePlan, SubscriptionBillingPlan, CustomEnterprisePlan


class PlanForm(forms.ModelForm):
    """Form for creating and editing subscription plans"""
    
    class Meta:
        model = Plan
        fields = ['name', 'description', 'price_monthly', 'price_yearly', 'max_users', 'max_storage_mb', 'max_projects', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'professional',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the key features and benefits of this plan',
                'required': False,
            }),
            'price_monthly': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '14,999',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
            'price_yearly': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '149,990',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
            'max_users': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1000',
                'min': '1',
                'required': True,
            }),
            'max_storage_mb': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '102400',
                'min': '0',
                'required': True,
            }),
            'max_projects': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '50',
                'min': '1',
                'required': True,
            }),
            'status': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'required': False,
            }),
        }

    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        price_monthly = cleaned_data.get('price_monthly')
        price_yearly = cleaned_data.get('price_yearly')
        max_storage_mb = cleaned_data.get('max_storage_mb')
        
        # Validate yearly price should not exceed 12x monthly price
        if price_monthly and price_yearly:
            max_allowed_yearly = float(price_monthly) * 12
            if float(price_yearly) > max_allowed_yearly:
                raise forms.ValidationError(
                    f'Yearly price should not exceed 12 times the monthly price '
                    f'(Maximum: {max_allowed_yearly:.2f})'
                )
        
        # Validate storage is not negative
        if max_storage_mb is not None and max_storage_mb < 0:
            raise forms.ValidationError('Storage cannot be negative.')
        
        return cleaned_data


class OneTimePlanForm(forms.ModelForm):
    """Form for creating and updating One-Time Plans"""
    
    class Meta:
        model = OneTimePlan
        fields = [
            'license_name',
            'one_time_price',
            'employee_limit',
            'admin_limit',
            'support_duration',
            'upgrade_eligible',
            'customers',
            'status'
        ]
        widgets = {
            'license_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., HRMS Core - Lifetime',
                'required': True
            }),
            'one_time_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price (₹)',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'employee_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of employees',
                'min': '1',
                'required': True
            }),
            'admin_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of admins',
                'min': '1',
                'required': True
            }),
            'support_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Support duration (months)',
                'min': '1',
                'required': True
            }),
            'upgrade_eligible': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'customers': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
                'required': True
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


class SubscriptionPlanForm(forms.ModelForm):
    """Form for creating and updating Subscription Plans"""
    
    class Meta:
        model = SubscriptionBillingPlan
        fields = [
            'company_name',
            'company_email',
            'billing_type',
            'add_on_category',
            'quantity',
            'max_quantity',
            'monthly_price',
            'subscription_status',
            'auto_renew'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name',
                'required': True
            }),
            'company_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'company@email.com',
                'required': True
            }),
            'billing_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'add_on_category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current quantity',
                'min': '0',
                'required': True
            }),
            'max_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum quantity',
                'min': '0',
                'required': True
            }),
            'monthly_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly price (₹)',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'subscription_status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'auto_renew': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].label_suffix = ""

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        max_quantity = cleaned_data.get('max_quantity')
        
        if quantity and max_quantity and quantity > max_quantity:
            raise forms.ValidationError(
                "Quantity cannot be greater than maximum quantity."
            )
        
        return cleaned_data


class CustomEnterprisePlanForm(forms.ModelForm):
    """Form for creating and updating Custom Enterprise Plans"""
    
    class Meta:
        model = CustomEnterprisePlan
        fields = [
            'company_name',
            'company_email',
            'plan_name',
            'employee_limit',
            'contract_duration',
            'monthly_price',
            'status'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name',
                'required': True
            }),
            'company_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'company@email.com',
                'required': True
            }),
            'plan_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Enterprise Plus, Full Access',
                'required': True
            }),
            'employee_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of employees',
                'min': '1',
                'required': True
            }),
            'contract_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contract duration (months)',
                'min': '1',
                'required': True
            }),
            'monthly_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly price (₹)',
                'step': '0.01',
                'min': '0',
                'required': True
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

