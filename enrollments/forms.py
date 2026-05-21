from django import forms
from .models import EnrollmentRequest


class EnrollmentRequestForm(forms.ModelForm):
    """
    Form used for submitting special enrollment requests.
    """

    class Meta:
        model = EnrollmentRequest

        # Only allow student to enter reason
        fields = ['reason']

        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Explain why you need special enrollment...'
            })
        }