from django import forms
from saas.models.feature import Feature


class FeatureForm(forms.ModelForm):
    """Form for creating/editing features"""
    class Meta:
        model = Feature
        fields = ['name', 'key', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CRM Module, Dashboard Analytics'
            }),
            'key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., crm_module, dashboard_analytics'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe this feature...'
            }),
        }
        help_texts = {
            'name': 'Display name for the feature',
            'key': 'Unique identifier (use lowercase and underscores)',
            'description': 'Optional description of what this feature provides'
        }
