# school/forms.py
from django import forms
from .models import Student

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'second_name', 'other_name', 'student_number', 'date_of_birth', 'gender']
