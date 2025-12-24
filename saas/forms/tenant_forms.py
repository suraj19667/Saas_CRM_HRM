from django import forms
from django.core.exceptions import ValidationError
from saas.models import Tenant, Plan


class TenantForm(forms.ModelForm):
    """Form for editing tenant details"""
    
    class Meta:
        model = Tenant
        fields = [
            'name',
            'status',
            'subscription_plan',
            'logo',
            'contact_email',
            'contact_phone', 
            'address',
            'allow_email_notifications',
            'allow_sms_notifications'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your company name'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[('active', 'Active'), ('inactive', 'Inactive')]),
            'subscription_plan': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@yourcompany.com'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your company address'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'allow_email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate subscription plan choices
        self.fields['subscription_plan'].queryset = Plan.objects.filter(status=True)
        self.fields['subscription_plan'].empty_label = "Select a plan"


class TenantCreationForm(forms.ModelForm):
    """Form for creating a new tenant/company"""
    
    class Meta:
        model = Tenant
        fields = [
            'name',
            'logo',
            'contact_email',
            'contact_phone', 
            'address',
            'allow_email_notifications',
            'allow_sms_notifications'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your company name',
                'required': True
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@yourcompany.com',
                'required': True
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your company address (optional)'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'allow_email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'name': 'Company Name *',
            'contact_email': 'Contact Email *',
            'contact_phone': 'Contact Phone *',
            'address': 'Company Address',
            'logo': 'Company Logo',
            'allow_email_notifications': 'Email Notifications',
            'allow_sms_notifications': 'SMS Notifications'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set help text
        self.fields['name'].help_text = 'This will be used to generate your unique domain'
        self.fields['logo'].help_text = 'Upload your company logo (optional). Max size: 2MB'
        self.fields['allow_email_notifications'].help_text = 'Receive important updates via email'
        self.fields['allow_sms_notifications'].help_text = 'Receive urgent notifications via SMS'
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError('Company name is required.')
        
        # Check for minimum length
        if len(name.strip()) < 2:
            raise ValidationError('Company name must be at least 2 characters long.')
        
        return name.strip()
    
    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email')
        if not email:
            raise ValidationError('Contact email is required.')
        
        return email.lower()
    
    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if not phone:
            raise ValidationError('Contact phone is required.')
        
        # Basic phone validation - remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if len(phone) < 10:
            raise ValidationError('Please enter a valid phone number.')
        
        return phone
    
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Check file size (2MB limit)
            if logo.size > 2 * 1024 * 1024:
                raise ValidationError('Logo file size cannot exceed 2MB.')
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not any(logo.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError('Logo must be a valid image file (JPG, PNG, GIF).')
        
        return logo