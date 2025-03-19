from django import forms
from .models import Fl_event, Fl_attendants

class Fl_eventForm(forms.ModelForm):
    attachments = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    class Meta:
        model = Fl_event
        fields = ['id','event_name', 'event_date', 'employer', 'employer_number','fl_advisors_involved', 'contact_person', 'designation',
       'contact_phone', 'contact_email', 'program', 'delivery_mode','on_spot_feedback']



class FlAttendantsForm(forms.ModelForm):
    class Meta:
        model = Fl_attendants
        fields = ['event_name', 'event_date']



class SearchMemberForm(forms.Form):
    q = forms.CharField(label='Search by name', max_length=100)

class RegisterAttendantForm(forms.Form):
    name = forms.CharField(max_length=100)
    #nssf_number = forms.CharField(max_length=20)
    # Add other fields as needed