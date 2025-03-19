from django.db import models
from django.contrib.auth.models import User
import datetime
from django_fsm import transition, FSMIntegerField, FSMField, transition
from django_fsm_log.decorators import fsm_log_by, fsm_log_description

# Create your models here.

def get_default_attachment():
    # Provide the path to the default attachment
    return 'attachments/default_file.pdf'


class Whistleblower(models.Model):
    TYPE_CHOICES = [
        ('Statement issues', 'Statement issues'),
        ('Non Payment', 'Non Payment'),
    ]
    profiling_choices=[
        ('Statement query', 'Statement query'),
        ('Non Registered Employer', 'Non Registered Employer'),
        ('Known member from a registered employer', 'Known member from a registered employer'),
        ('UnKnown member from a registered employer', 'UnKnown member from a registered employer'),
    ]
  

    key = models.CharField(max_length=255, unique=True)
    nssf_number = models.CharField(max_length=900)
    type = models.CharField(max_length=900)
    date_submitted = models.DateTimeField()
    last_update = models.DateTimeField()
    user_id = models.CharField(max_length=900, blank=True, null=True)
    company_number = models.CharField(max_length=9000)
    company_name = models.CharField(max_length=9000)
    number_employees = models.CharField(max_length=900)
    physical_address = models.TextField()
    director = models.CharField(max_length=9000)
    short_title = models.TextField()
    description = models.TextField()
    other_info = models.TextField()
    status = models.CharField(max_length=100, blank=True, null=True)
    auditor_name = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField()
    auditor_id = models.CharField(max_length=255, blank=True, null=True)


    profile = models.CharField(max_length=100, choices=profiling_choices, blank=True, null=True)
    updated_nssf_number = models.CharField(max_length=255, blank=True, null=True)
    updated_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True, null=True)
    updated_company_number = models.CharField(max_length=255, blank=True, null=True)
    updated_company_name = models.CharField(max_length=255, blank=True, null=True)
    updated_anonymous = models.BooleanField(default=False,null=True)
    updated_member_contact = models.CharField(max_length=15, blank=True, null=True)
    updated_member_email = models.EmailField(blank=True, null=True)
    updated_work_from_date = models.DateField(blank=True, null=True)
    updated_work_to_date = models.DateField(blank=True, null=True)
    ongoing_audit = models.BooleanField(default=False,null=True)
    ongoing_auditor = models.CharField(max_length=255, blank=True, null=True)
    last_audit_date = models.DateField(blank=True, null=True)
    in_legal = models.BooleanField(default=False,null=True)
    registered_employer = models.BooleanField(default=False,null=True)
    extra_info = models.TextField(blank=True, null=True)
    #stage = models.CharField(max_length=100, blank=True, null=True)
    audited_recently_or_in_legal = models.BooleanField(default=False, null=True)
    work_scope_known = models.BooleanField(default=False, null=True)
    case_profiling_result = models.CharField(max_length=255, blank=True, null=True)
    CRM_case_number = models.CharField(max_length=255, blank=True, null=True)
    #confirmed_status = models.CharField(max_length=255,blank=True, null=True)
    bi_auditor_username	= models.CharField(max_length=255, blank=True, null=True)
    bi_auditor_user_id = models.CharField(max_length=900, blank=True, null=True)




    def __str__(self):
        return self.key



class Comment(models.Model):
    key = models.CharField(max_length=255)  # Adjust length as needed
    comment = models.TextField()
    from_user_id = models.CharField(max_length=255, blank=True, null=True)  # Optional field
    date_added = models.DateTimeField(auto_now_add=True)
    comment_mode = models.CharField(max_length=50)  # Adjust choices or length as needed
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver_email = models.EmailField(blank=True, null=True)  # Optional field
    receiver_phone = models.CharField(max_length=20, blank=True, null=True)  # Optional field

    def __str__(self):
        return f"Comment by {self.user.username} on {self.date_added}"
    
    
class WhistleblowerLog(models.Model):
    # Define your model fields here
    #model = models.ForeignKey(Whistleblower, on_delete=models.CASCADE, related_name='logs')
    whistleblower = models.ForeignKey(Whistleblower, on_delete=models.CASCADE, related_name='logs')  # Add this field
    key = models.CharField(max_length=255)  # Adjust length as needed
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    review_status = models.CharField(max_length=255,blank=True, null=True)
    confirmed_status = models.CharField(max_length=255,blank=True, null=True)

class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    #forclosure = models.ForeignKey('Forclosure', on_delete=models.CASCADE, related_name='attachments')
    whistleblowerLog = models.ForeignKey('WhistleblowerLog', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)