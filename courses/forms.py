from django import forms
from django.contrib.auth import get_user_model
from .models import Course

User = get_user_model()


class CourseForm(forms.ModelForm):
    instructor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='instructor'),
        required=False,
        empty_label="--- Select Instructor ---"
    )

    prerequisites = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Course
        fields = ['name', 'course_code', 'description', 'seating_limit', 'start_time', 'end_time', 'instructor', 'prerequisites']

class InstructorCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['description', 'seating_limit', 'start_time', 'end_time']