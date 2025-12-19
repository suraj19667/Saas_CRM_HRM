from django import forms
from saas.models.planfeature import PlanFeature
from saas.models.feature import Feature
from saas.models.plan import Plan


class PlanFeatureForm(forms.ModelForm):
    """Form for adding/editing individual plan features"""
    class Meta:
        model = PlanFeature
        fields = ['feature', 'feature_limit']
        widgets = {
            'feature': forms.Select(attrs={'class': 'form-control'}),
            'feature_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave empty for unlimited',
                'min': '0'
            }),
        }
        help_texts = {
            'feature_limit': 'Maximum limit for this feature. Leave empty for unlimited access.'
        }


class PlanFeatureInlineForm(forms.Form):
    """Form for managing multiple features for a plan"""
    feature = forms.ModelChoiceField(
        queryset=Feature.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    feature_limit = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Unlimited',
            'min': '0'
        }),
        help_text='Leave empty for unlimited'
    )
    
    def __init__(self, *args, **kwargs):
        plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        
        # Exclude features already added to the plan
        if plan:
            existing_feature_ids = PlanFeature.objects.filter(
                plan=plan
            ).values_list('feature_id', flat=True)
            self.fields['feature'].queryset = Feature.objects.exclude(
                id__in=existing_feature_ids
            )

