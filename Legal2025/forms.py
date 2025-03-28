from django import forms
from .models import LegalFiles,ReconciliationAgreement, Installment, Payment,Comment, HearingEvent
from django.apps import apps  # ✅ Lazy Import Fix
from django.core.exceptions import ValidationError
import re
from .utils import get_trn_payments  # Import function to fetch TRN details
from django.forms import inlineformset_factory



class LegalFilesForm(forms.ModelForm):
    class Meta:
        model = LegalFiles
        fields = [
            'fy_submitted_to_legal', 
            'fy_deed_signed', 
            'source', 
            'legal_status', 
            'employer_name', 
            'nssf_number', 
            'advocate', 
            'auditor', 
            'branch', 
            'audited_period_startdate', 
            'audited_period_enddate', 
            'total_arrears', 
            'special_contribution', 
            'interest', 
            'penalties', 
            'ten_percent_penalty', 
            'amount_paid', 
            'balance', 
            'date_received', 
            'detailed_status', 
            'court', 
            'courtfiling_date', 
            'closure_date'
        ]  # Add all fields you want to include in the form
        widgets = {
            'fy_submitted_to_legal': forms.Select(attrs={'class': 'form-select'}),
            'fy_deed_signed': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'legal_status': forms.Select(attrs={'class': 'form-select'}),
            'employer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employer Name'}),
            'nssf_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NSSF Number'}),
            'advocate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Advocate Name'}),
            'auditor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auditor Name'}),
            'branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch'}),
            'audited_period_startdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audited_period_enddate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_arrears': forms.NumberInput(attrs={'class': 'form-control'}),
            'special_contribution': forms.NumberInput(attrs={'class': 'form-control'}),
            'interest': forms.NumberInput(attrs={'class': 'form-control'}),
            'penalties': forms.NumberInput(attrs={'class': 'form-control'}),
            'ten_percent_penalty': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_received': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'detailed_status': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'court': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Court'}),
            'courtfiling_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'closure_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

#Legal File Update form
class LegalFileUpdateForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, required=True)
    legal_status = forms.ChoiceField(choices=LegalFiles.LEGAL_STATUS_CHOICES, required=True)
    attachments = forms.FileField(required=False)
    
    class Meta:
        model = LegalFiles

class LegalFileUpdateFormmanager(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, required=True)
   
    
    class Meta:
        model = LegalFiles

class LitigationForm(forms.ModelForm):
    class Meta:
        model = LegalFiles
        fields = ['court','courtfiling_date','nexthearing_date'] 

class FullyPaidForm(forms.ModelForm):
    class Meta:
        model = LegalFiles
        fields = ['amount_paid','balance'] 


class ReconciliationAgreementForm(forms.ModelForm):
    legal_file = forms.ModelChoiceField(
        queryset=LegalFiles.objects.all(),
        empty_label="Select a Legal File",
        widget=forms.Select(attrs={'class': 'form-control', 'readonly': 'readonly'})  # Readonly Field
    )

    class Meta:
        model = ReconciliationAgreement
        fields = ['legal_file', 'total_arrears', 'total_interest', 'penalty_10percent']
        widgets = {
            'total_arrears': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_interest': forms.NumberInput(attrs={'class': 'form-control'}),
            'penalty_10percent': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'audited_period_startdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # 'audited_period_enddate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        legal_file = kwargs.pop('legal_file', None)  # Get the legal_file passed from view
        super(ReconciliationAgreementForm, self).__init__(*args, **kwargs)

        if legal_file:
            self.fields['legal_file'].initial = legal_file  # Pre-fill Employer Name
            self.fields['legal_file'].widget.attrs['disabled'] = True  # Make Read-Only

class InstallmentForm(forms.ModelForm):
    class Meta:
        model = Installment
        fields = ['date_of_payment', 'amount', 'description']
        widgets = {
            'date_of_payment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),  
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

InstallmentFormSet = inlineformset_factory(ReconciliationAgreement, Installment, form=InstallmentForm, extra=1, can_delete=True)

class InstallmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Installment
        fields = ['description']  # Status is removed
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class PaymentForm(forms.ModelForm):
    transaction_reference_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    amount_paid = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    class Meta:
        model = Payment
        fields = ['transaction_reference_number', 'amount_paid', 'payment_date']

    def __init__(self, *args, nssf_number=None, legal_start_date=None, legal_end_date=None, **kwargs):
        """Initialize the form with extra validation parameters."""
        super().__init__(*args, **kwargs)
        self.nssf_number = nssf_number
        self.legal_start_date = legal_start_date
        self.legal_end_date = legal_end_date

    def clean_transaction_reference_number(self):
        """Validate TRN format and fetch payment details from the external database."""
        trn = self.cleaned_data.get('transaction_reference_number')

        if not all([self.nssf_number, self.legal_start_date, self.legal_end_date]):
            raise ValidationError("Missing required data for TRN validation.")

        # Validate TRN format
        pattern = r'^NSSF\d{10}$'
        if not re.match(pattern, trn):
            raise ValidationError("Transaction Reference Number must be in the format: NSSFxxxxxxxxxx")

        # Fetch TRN details
        trn_data = get_trn_payments(self.nssf_number, trn, self.legal_start_date, self.legal_end_date)

        if not trn_data or trn_data.get('total_payment', 0) == 0:
            raise ValidationError("Invalid TRN or no payment found in the external database.")

        # ✅ Assign payment data to cleaned_data
        self.cleaned_data['amount_paid'] = trn_data.get('total_payment', 0)
        self.cleaned_data['payment_date'] = trn_data.get('payment_date', None)

        return trn

    def save(self, commit=True):
        """Ensure that the payment saves correctly to the database."""
        instance = super().save(commit=False)
        instance.amount_paid = self.cleaned_data.get('amount_paid', 0)
        instance.payment_date = self.cleaned_data.get('payment_date', None)

        # 🔍 Debugging: Check if data is actually being saved
        print(f"✅ Saving Payment: {instance.transaction_reference_number} | Amount: {instance.amount_paid}")

        if commit:
            instance.save()
            print("✅ Payment saved successfully.")

        return instance


"""Hearing Events"""
class HearingEventForm(forms.ModelForm):
    class Meta:
        model = HearingEvent
        fields = ['legal_file', 'nexthearing_date', 'description']
        widgets = {
            'legal_file': forms.Select(attrs={'class': 'form-control'}),
            'nexthearing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
