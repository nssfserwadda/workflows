from django import forms
#from django.contrib.auth.forms import UserCreationForm
#from django.contrib.auth.models import User
from .models import Suspense, SuspenseSummary



class SearchSuspenseForm(forms.Form):
    q = forms.CharField(label='Search by member name', max_length=100) 



class EmpSearchSuspenseForm(forms.Form):
    q = forms.CharField(label='Search by employer name', max_length=100) 


class NsfSearchSuspenseForm(forms.Form):
    q = forms.CharField(label='Search by employer NSSFNO', max_length=100)

    

class NsfSummarySearchForm(forms.Form):
    q = forms.CharField(label='Search by employer name', max_length=100)


