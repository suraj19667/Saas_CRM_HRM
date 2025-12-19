from django import forms
from saas.models.subscription import SubscriptionPlan
import json

class SubscriptionPlanForm(forms.ModelForm):
    features = forms.CharField(widget=forms.Textarea, help_text="Enter features as JSON array, e.g. ['Feature 1', 'Feature 2']")

    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'price', 'duration_days', 'features']

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('Price must be greater than 0.')
        return price

    def clean_duration_days(self):
        duration = self.cleaned_data['duration_days']
        if duration not in [30, 90, 365]:
            raise forms.ValidationError('Duration must be 30, 90, or 365 days.')
        return duration

    def clean_features(self):
        features = self.cleaned_data['features']
        try:
            features_json = json.loads(features)
            if not isinstance(features_json, list):
                raise forms.ValidationError('Features must be a JSON array.')
        except Exception:
            raise forms.ValidationError('Enter valid JSON array for features.')
        return features_json

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['features'].initial = json.dumps(self.instance.features, indent=2)
