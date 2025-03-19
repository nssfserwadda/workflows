from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Start Date'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='End Date'
    )
    employer_nssf_number = forms.CharField(
        max_length=50,  # Adjust length as needed
        label='Employer NSSF Number',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Employer NSSF Number'})
    )