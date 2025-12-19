from django import forms
from saas.models.plan import Plan


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'description', 'price_monthly', 'price_yearly', 'max_users', 'max_storage_mb', 'max_projects', 'status']
