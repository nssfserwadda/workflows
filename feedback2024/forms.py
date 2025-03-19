# your_app_name/forms.py
from django import forms
from .models import Whistleblower, WhistleblowerLog




class OptionSelectionForm(forms.Form):
    RECONCILE_CHOICES = [
        ('Non Registered Employer', 'Non resgistered employer'),
        ('statement_querry_case', 'Statement querry case'),
        ('registered_employer', 'Registered Employer'),
    ]
    option = forms.ChoiceField(choices=RECONCILE_CHOICES, widget=forms.RadioSelect)

class Option1Form(forms.Form):
    registered_employer = forms.CharField(max_length=100)
    

class Option2Form(forms.Form):
    statement_querry_CRM_id = forms.CharField(max_length=100)
    

class Option3Form(forms.Form):
    field_5 = forms.CharField(widget=forms.Textarea)
    field_6 = forms.BooleanField(required=False)




class WhistleblowerUpdateForm(forms.ModelForm):
    class Meta:
        model = Whistleblower
        fields = [
            'extra_info', 'in_legal', 'last_audit_date', 'ongoing_audit',
            'ongoing_auditor', 'registered_employer',  'updated_anonymous','updated_company_name', 'updated_company_number',
            'updated_member_contact', 'updated_member_email', 'updated_nssf_number',
            'updated_type', 'updated_work_from_date', 'updated_work_to_date'
        ]
        widgets = {
            'last_audit_date': forms.DateInput(attrs={'type': 'date'}),
            'updated_work_from_date': forms.DateInput(attrs={'type': 'date'}),
            'updated_work_to_date': forms.DateInput(attrs={'type': 'date'}),
        }


class WhistleblowerClosureForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('audit_ongoing', 'Audit Ongoing'),
        ('deed_signed', 'Deed Signed'),
        ('under_legal', 'Under Legal'),
        ('direct_demand', 'Direct Demand'),
        ('fully_settled', 'Fully Settled'),
    ]


    attachments = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=True)

    class Meta:
        model = WhistleblowerLog
        fields = ['comment','status']

class WhistleblowerReviewForm(forms.Form):
    REVIEW_CHOICES = [
        ('confirmed', 'Confirm Status'),
        ('disputed', 'Dispute Status'),
    ]
    
    decision = forms.ChoiceField(choices=REVIEW_CHOICES, widget=forms.Select)
    comment = forms.CharField(widget=forms.Textarea, required=False)  # Comment is optional


class BaseProfilingForm(forms.ModelForm):
    class Meta:
        model = Whistleblower
        fields = ['profile']  # This allows the user to select the profile choice.

class StatementQueryForm(forms.ModelForm):
    class Meta:
        model = Whistleblower
        fields = ['CRM_case_number']

class EmployerNotRegisteredForm(forms.ModelForm):
    class Meta:
        model = Whistleblower
        fields = ['updated_company_name']

class EmployerRegisteredMemberKnownForm(forms.ModelForm):
    class Meta:
        model = Whistleblower
        fields = [
            'updated_company_number', 'updated_company_name', 'updated_member_contact', 
            'updated_nssf_number', 'ongoing_audit', 'ongoing_auditor', 'work_scope_known', 
            'updated_work_from_date', 'updated_work_to_date', 'audited_recently_or_in_legal'
        ]
        # Add logic to make fields conditionally required if necessary
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if ongoing_audit is True, then ongoing_auditor is required
        ongoing_audit = cleaned_data.get('ongoing_audit')
        ongoing_auditor = cleaned_data.get('ongoing_auditor')
        
        if ongoing_audit and not ongoing_auditor:
            self.add_error('ongoing_auditor', 'Ongoing auditor is required when ongoing audit is True.')

        # Check if work_scope_known is True, then updated_work_from_date and updated_work_to_date are required
        work_scope_known = cleaned_data.get('work_scope_known')
        updated_work_from_date = cleaned_data.get('updated_work_from_date')
        updated_work_to_date = cleaned_data.get('updated_work_to_date')

        if work_scope_known:
            if not updated_work_from_date:
                self.add_error('updated_work_from_date', 'Work from date is required when work scope is known.')
            if not updated_work_to_date:
                self.add_error('updated_work_to_date', 'Work to date is required when work scope is known.')

        return cleaned_data
    
class EmployerRegisteredMemberAnonymousForm(forms.ModelForm):
    class Meta:
        model = Whistleblower
        fields = [
            'updated_company_number', 'updated_company_name', 'ongoing_audit', 
            'ongoing_auditor', 'work_scope_known', 'updated_work_from_date', 
            'updated_work_to_date', 'audited_recently_or_in_legal'
        ]