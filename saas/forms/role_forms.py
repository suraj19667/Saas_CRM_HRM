from django import forms
from ..models import Role

class RoleForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter role name'}),
        label="Role Name"
    )

    class Meta:
        model = Role
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter role description', 'rows': 3}),
        }
