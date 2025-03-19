from django.db import models
from django_fsm import transition, FSMIntegerField, FSMField, transition
from django_fsm_log.decorators import fsm_log_by, fsm_log_description
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import pandas as pd
from django.contrib.contenttypes.models import ContentType
from multiselectfield import MultiSelectField
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

def get_default_attachment():
    # Provide the path to the default attachment
    return 'attachments/default_file.pdf'


User = get_user_model()

class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    #forclosure = models.ForeignKey('Forclosure', on_delete=models.CASCADE, related_name='attachments')
    forclosure = models.ForeignKey('Forclosure', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)
    engagement = models.ForeignKey('Engagement', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)
    generalcase = models.ForeignKey('Generalcase', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)
    #generalquery = models.ForeignKey('Generalquery', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)


class Forclosure(models.Model):
    STATE_CHOICES = (
        ('initiated', 'Initiated'),
        ('cancelled', 'Cancelled'),
        ('first_reviewed', 'First_reviewed'),
        ('resubmited', 'Resubmited'),
        ('assigned', 'Assigned'),
        ('rejected', 'Rejected'),
        ('reversed', 'Reversed'),
        ('approved', 'Approved'),        
    )

    REASON_CHOICES = (
        ('nira', 'Employer closed in NIRA'),
        ('others', 'Others'),
       
    )

    state = FSMField(default='initiated', choices=STATE_CHOICES)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
   


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forclosures')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_forclosures', limit_choices_to={'groups__name': 'Supervisors'})
    next_action_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='next_action_forclosures', blank=True, null=True, limit_choices_to={'groups__name': 'Assessors'})
    employer_name = models.CharField(max_length=130)
    nssf_no = models.CharField(max_length=130)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    #attachment = models.FileField(upload_to='attachments/', blank=False, null=False)
    #attachment = models.FileField(upload_to='attachments/', default=get_default_attachment)
    remark = models.TextField(blank=True)
    review_comment = models.TextField(blank=True)



    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source=['initiated','reversed','resubmited'], target='cancelled')
    def cancel(self,user,review_comment):
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='cancel', review_comment=review_comment)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source=['initiated','resubmited'], target='first_reviewed')
    def first_review(self,user,review_comment):        
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='first_review', review_comment=review_comment)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='assigned', target= 'approved')
    def approve(self,user,review_comment):
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='approve', review_comment=review_comment)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source=['initiated', 'assigned','resubmited'], target='reversed')
    def reverse(self,user,review_comment):
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='reverse', review_comment=review_comment)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='reversed', target='resubmited')
    def resubmit(self,user,review_comment):
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='resubmit', review_comment=review_comment)
        #pass



    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source=['initiated', 'assigned'], target='rejected')
    def reject(self,user,review_comment):
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='reject', review_comment=review_comment)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='first_reviewed', target='assigned')
    def assign(self, user, next_action_user, review_comment):
        self.next_action_user = next_action_user
        self.review_comment = review_comment
        self.save()
        ForclosureLog.objects.create(model=self, user=user, action='assign', review_comment=review_comment)
        #pass

    def save(self, *args, **kwargs):
        if not self.pk:  # Check if it's a new instance (not yet saved to the database)
            self.updated_at = self.created_at
        super(Forclosure, self).save(*args, **kwargs)


class ForclosureLog(models.Model):
    # Define your model fields here
    model = models.ForeignKey(Forclosure, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forclosure_logs')
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    #user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='forclosure_logs')
    #user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')    
    review_comment = models.TextField()
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
  

class Employer(models.Model):
    party_role_id = models.IntegerField()
    nssf_no = models.CharField(max_length=255)
    employer_name = models.CharField(max_length=255)
    registry_dt = models.DateField(null=True, blank=True)
    party_role_type_descr = models.CharField(max_length=255)
    # Add other fields as needed

    def save(self, *args, **kwargs):
        if pd.isnull(self.registry_dt):
            self.registry_dt = None  # Set None instead of "NaT"
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'employers'


class Engagement(models.Model):
    ACTIVITY_CHOICES = (
        ('account4noncompliance','Account for non-compliance'),
        ('member_reg', 'Member registration'),
        ('assessment', 'Assessment'),
        ('fl', 'Financial Literacy'),

        ('roadshow', 'Roadshow'),
        ('audit', 'Compliance Audit'),
        ('inspection', 'Inspection'),
        ('senstisation', 'Senstisation'),
        ('support', 'Support'),
        ('recovery', 'Collections recovery'),
        ('emp_reg', 'Employer registration'),
        ('mapping', 'Mapping'),
        ('suspe', 'Suspence clearence'),
        ('closure', 'Employer closure'),
        
    )

    STATE_CHOICES = (
        ('recorded', 'Recorded'),
        ('forwarded', 'forwarded'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),        
    )

    MAIN_CHOICES = (
        ('account4noncompliance','Account for non-compliance'),
        ('member_reg', 'Member registration'),
        ('legal', 'Record legal case'),         
    )


    state = FSMField(default='recorded', choices=STATE_CHOICES)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagements')
    employer_name = models.CharField(max_length=130)
    nssf_no = models.CharField(max_length=130)
    main_activity = models.CharField(max_length=100, choices=MAIN_CHOICES, blank=True, null=True)

    activity_done = MultiSelectField(choices=ACTIVITY_CHOICES, max_choices=11)
    action_date = models.DateField(null=True, blank=True)
    
    engaged_mobile = models.CharField(max_length=20, blank=True, null=True)  # New field for engaged mobile
    engaged_email = models.EmailField(blank=True, null=True)  # New field for engaged email


    #attachment = models.FileField(upload_to='attachments/', blank=False, null=False)
    #attachment = models.FileField(upload_to='attachments/', default=get_default_attachment)
    comment = models.TextField(blank=True)
    remark = models.TextField(blank=True)
    #next_action_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='next_action_engagements', blank=True, null=True)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_engagements',blank=True, null=True)#, limit_choices_to={'groups__name': 'Supervisors'})
    #created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_engagements')

    REASON_CHOICES = (
        ('inconsistent_funding', 'Inconsistent funding from government/donors'),
        ('covid19_effects', 'Covid-19 effects'),
        ('economic_strain', 'Economic strain and cash flow challenges'),
        ('employer_not_started', 'Employer was registered but hasn’t started operating'),
        ('unable_to_locate_employer', 'Inability to locate employer/briefcase company'),
        ('hard_to_reach_employer', 'Hard to reach employer (very far)'),
        ('high_employer_to_rm_ratio', 'High employer to RM ratio'),
        ('ignorance_of_nssf_law', 'Ignorance of the NSSF law'),
        ('informal_employer_closure', 'Informal employer closure'),
        ('informal_employments', 'Informal employments (casual laborers)'),
        ('lack_of_trust_in_nssf', 'Lack of trust in the NSSF brand'),
        ('non_payment_during_school_holidays', 'Non-payment during school holidays'),
        ('system_breakdown', 'Painful system experiences and breakdown/internet connectivity issues'),
        ('political_instability', 'Political instability'),
        ('political_interference', 'Political interference and restricted access to employer premises'),
        ('stubborn_employer', 'Stubborn and adamant employer'),
        ('unfavorable_registration_requirements', 'Unfavorable registration requirements for new members and employers'),
    )

    reason_for_non_compliance = models.CharField(max_length=50, choices=REASON_CHOICES, blank=True, null=True)


    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='recorded', target='forwarded')
    def forward(self,user, reviewer):
        #self.remark = remark
        self.reviewer = reviewer
        self.save()
        EngagementLog.objects.create(model=self, user=user, action='forward')
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='recorded', target='cancelled')
    def cancel(self,user):
        #self.remark = remark
        self.save()
        EngagementLog.objects.create(model=self, user=user, action='cancel')
        #pass


    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='forwarded', target='rejected')
    def reject(self,user,remark):
        self.remark = remark
        self.save()
        EngagementLog.objects.create(model=self, user=user, action='reject', remark=remark)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='forwarded', target= 'approved')
    def approve(self,user,remark):
        self.remark = remark
        self.save()
        EngagementLog.objects.create(model=self, user=user, action='approve', remark=remark)
        #pass




class EngagementLog(models.Model):
    # Define your model fields here
    model = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_logs')  
    remark = models.TextField()
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
   

class Generalcase(models.Model):

    STATE_CHOICES = (
        ('recorded', 'Recorded'),
        ('forwarded', 'forwarded'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),        
    )

    state = FSMField(default='recorded', choices=STATE_CHOICES)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generalcases')
    subject = models.CharField(max_length=130)
    action_date = models.DateTimeField()
    any_other_info = models.CharField(max_length=130)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_generalcases',blank=True, null=True)#, limit_choices_to={'groups__name': 'Supervisors'})
    #next_action_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='next_action_generalcases', blank=True, null=True, limit_choices_to={'groups__name': 'Assessors'})    
    remark = models.TextField(blank=True)
    comment = models.TextField(blank=True)

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='recorded', target='forwarded')
    def forward(self,user, reviewer):
        #self.remark = remark
        self.reviewer = reviewer
        self.save()
        GeneralcaseLog.objects.create(model=self, user=user, action='forward')
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='recorded', target='cancelled')
    def cancel(self,user):
        #self.remark = remark
        self.save()
        GeneralcaseLog.objects.create(model=self, user=user, action='cancel')
        #pass


    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='forwarded', target='rejected')
    def reject(self,user,remark):
        self.remark = remark
        self.save()
        GeneralcaseLog.objects.create(model=self, user=user, action='reject', remark=remark)
        #pass

    @fsm_log_by
    @fsm_log_description
    @transition(field=state, source='forwarded', target= 'approved')
    def approve(self,user,remark):
        self.remark = remark
        self.save()
        GeneralcaseLog.objects.create(model=self, user=user, action='approve', remark=remark)
        #pass

class GeneralcaseLog(models.Model):
    # Define your model fields here
    model = models.ForeignKey(Generalcase, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generalcase_logs')  
    remark = models.TextField()
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class Rating(models.Model):
    value = models.IntegerField()

class Getfeedback(models.Model):
    fcr_resolved = models.BooleanField(null=True, blank=True)
    nps_rating = models.IntegerField(null=True, blank=True)
    ces_easy = models.BooleanField(null=True, blank=True)
    overall_satisfaction = models.BooleanField(null=True, blank=True)
    additional_comments = models.TextField(null=True, blank=True)

class Feedback3(models.Model):
    rating = models.IntegerField(default=0)


class Feedback4(models.Model):
    rating = models.IntegerField()
    fcr_resolved = models.BooleanField(null=True, blank=True)
    ces_easy = models.IntegerField(choices=[(1, 'Very hard'), (2, 'Hard'), (3, 'Easy'), (4, 'Very easy')],null=True, blank=True)
    overall_satisfaction = models.IntegerField(choices=[(0, 'Not satisfied'), (1, 'Satisfied')],null=True, blank=True)
    additional_comments = models.TextField(blank=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    #phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"Feedback4 - {self.pk}"
    



class Traffic(models.Model):
    contact_date = models.DateField()
    nssf_number = models.CharField(max_length=20)
    channel = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    reason = models.TextField()
    served_by = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.contact_date}"



class Outbound(models.Model):
    CHANNEL_CHOICES = [
        ('Walkin', 'Walkin'),
        ('Call center', 'Call Quality'),
        ('Online', 'Online'),
        ('NPS', 'NPS'),
        ('Look & Feel', 'Look & Feel'),
        ('First contact resolution', 'First contact resolution'),
    ]    
    channel = models.CharField(max_length=100, choices=CHANNEL_CHOICES)
        
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_contact = models.CharField(max_length=15, null=True, blank=True)
    nssf_number = models.CharField(max_length=20, null=True, blank=True)
    served_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Outbound_served_by', limit_choices_to={'groups__name': 'Supervisors'})
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outbound_user')

    nps = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)

    fcr_resolved = models.IntegerField(choices=[(1, 'Yes'), (0, 'No')], null=True, blank=True)
    ces_easy = models.IntegerField(choices=[(1, 'Very hard'), (2, 'Hard'), (3, 'Easy'), (4, 'Very easy')], null=True, blank=True)
    overall_satisfaction = models.IntegerField(choices=[(0, 'Not satisfied'), (1, 'Satisfied')], null=True, blank=True)
    additional_comments = models.TextField(blank=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New Fields
    BRANCH_CHOICES = [
        ('Acacia', 'Acacia'),
        ('Arua', 'Arua'),
        ('Bakuli', 'Bakuli'),
        ('Bugolobi', 'Bugolobi'),
        ('Customer Service Center', 'Customer Service Center'),
        ('Entebbe', 'Entebbe'),
        ('Fort Portal', 'Fort Portal'),
        ('Gulu', 'Gulu'),
        ('Hoima', 'Hoima'),
        ('Ishaka', 'Ishaka'),
        ('Jinja', 'Jinja'),
        ('Kabale', 'Kabale'),
        ('Kampala City', 'Kampala City'),
        ('Lira', 'Lira'),
        ('Masaka', 'Masaka'),
        ('Masindi', 'Masindi'),
        ('Mbale', 'Mbale'),
        ('Mbarara', 'Mbarara'),
        ('Moroto', 'Moroto'),
        ('Mukono', 'Mukono'),
        ('Soroti', 'Soroti'),
        ('Tororo', 'Tororo'),
    ]
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)

    REASON_CHOICES = [
        ('Balance request', 'Balance request'),
        ('Benefits follow up', 'Benefits follow up'),
        ('Benefits verification', 'Benefits verification'),
        ('Call Center login/logout', 'Call Center login/logout'),
        ('Claim inquiry', 'Claim inquiry'),
        ('Claim received', 'Claim received'),
        ('Clearance certificate', 'Clearance certificate'),
        ('Clearance of sheet B', 'Clearance of sheet B'),
        ('Compliance Audit', 'Compliance Audit'),
        ('Conduct roadshows', 'Conduct roadshows'),
        ('Contact update', 'Contact update'),
        ('Contributions receipting', 'Contributions receipting'),
        ('Corporate social responsibility', 'Corporate social responsibility'),
        ('COVID Invalidity benefits', 'COVID Invalidity benefits'),
        ('COVID Survivor’s benefits', 'COVID Survivor’s benefits'),
        ('Customer engagement message', 'Customer engagement message'),
        ('Discussion of draft audit report', 'Discussion of draft audit report'),
        ('Docked Pas claims', 'Docked Pas claims'),
        ('Duplicate cards', 'Duplicate cards'),
        ('Employee engagement collection', 'Employee engagement collection'),
        ('Employee registration', 'Employee registration'),
        ('Employer registration', 'Employer registration'),
        ('Financial literacy', 'Financial literacy'),
        ('General inquiry', 'General inquiry'),
        ('Inspection of employers', 'Inspection of employers'),
        ('Issuing clearance certificate', 'Issuing clearance certificate'),
        ('KYC Updates', 'KYC Updates'),
        ('Member details update', 'Member details update'),
        ('Midterm access inquiry', 'Midterm access inquiry'),
        ('Midterm claim follow up', 'Midterm claim follow up'),
        ('Midterm claim received', 'Midterm claim received'),
        ('No show customer', 'No show customer'),
        ('NSSF number retrieval', 'NSSF number retrieval'),
        ('NSSF Smart card', 'NSSF Smart card'),
        ('Office location', 'Office location'),
        ('Office opening hours', 'Office opening hours'),
        ('Outbound escalation', 'Outbound escalation'),
        ('Real estate inquiry', 'Real estate inquiry'),
        ('Self assessment test (SAT)', 'Self assessment test (SAT)'),
        ('Sensitization', 'Sensitization'),
        ('SmartLife', 'SmartLife'),
        ('Spam mail.', 'Spam mail.'),
        ('Statement request', 'Statement request'),
        ('Statement enquiries', 'Statement enquiries'),
        ('Statement update', 'Statement update'),
        ('Unsuccessful calls', 'Unsuccessful calls'),
        ('Voluntary company registration', 'Voluntary company registration'),
        ('Voluntary inquiry', 'Voluntary inquiry'),
        ('Voluntary member registration', 'Voluntary member registration'),
        ('Whistleblower', 'Whistleblower'),
    ]
    reason_for_visit = models.CharField(max_length=100, choices=REASON_CHOICES, null=True, blank=True)

    verbatim_rating = models.TextField(blank=True, null=True)

    FRONT_OFFICE_CHOICES = [
        ('Good/positive CSO attitude', 'Good/positive CSO attitude'),
        ('Poor/negative attitude', 'Poor/negative attitude'),
        ('Good/clear CSO explanation', 'Good/clear CSO explanation'),
        ('Poor/unclear CSO explanation', 'Poor/unclear CSO explanation'),
        ('Fast/Quick CSO handling time', 'Fast/Quick CSO handling time'),
        ('Slow/delayed CSO handling time', 'Slow/delayed CSO handling time'),
        ('CSO knowledgeable', 'CSO knowledgeable'),
        ('CSO not knowledgeable', 'CSO not knowledgeable'),
        ('Good CSO listening skills', 'Good CSO listening skills'),
        ('Poor CSO listening skill', 'Poor CSO listening skill'),
        ('Full CSO attention', 'Full CSO attention'),
        ('Divided CSO attention', 'Divided CSO attention'),
        ('Quick/Good CSO resolution', 'Quick/Good CSO resolution'),
        ('Good CSO skill', 'Good CSO skill'),
        ('Poor CSO skill', 'Poor CSO skill'),
        ('Nothing extra ordinary', 'Nothing extra ordinary'),
        ('None', 'None'),
    ]
    front_office_reasons = models.CharField(max_length=100, choices=FRONT_OFFICE_CHOICES, null=True, blank=True)

    BACK_OFFICE_CHOICES = [
        ('Easy finding and recognizing', 'Easy finding and recognizing'),
        ('Difficult finding and recognizing', 'Difficult finding and recognizing'),
        ('Quick/Fast escalation process', 'Quick/Fast escalation process'),
        ('Slow/poor escalation process', 'Slow/poor escalation process'),
        ('Up to date contributions', 'Up to date contributions'),
        ('Missing contributions', 'Missing contributions'),
        ('Fast Benefits process', 'Fast Benefits process'),
        ('Slow/delayed benefits process', 'Slow/delayed benefits process'),
        ('Process simplicity', 'Process simplicity'),
        ('Process difficulty', 'Process difficulty'),
        ('System is fast and stable', 'System is fast and stable'),
        ('System is slow and unstable', 'System is slow and unstable'),
        ('Acceptable waiting time', 'Acceptable waiting time'),
        ('Long waiting time', 'Long waiting time'),
        ('Limited product offering', 'Limited product offering'),
        ('Limited language offering', 'Limited language offering'),
        ('Wrong interest calculation', 'Wrong interest calculation'),
        ('Good/high interest', 'Good/high interest'),
        ('Poor/low interest', 'Poor/low interest'),
        ('Positive organizational reputation', 'Positive organizational reputation'),
        ('Negative organizational reputation', 'Negative organizational reputation'),
        ('Delayed system updates', 'Delayed system updates'),
        ('None', 'None'),
    ]
    back_office_reasons = models.CharField(max_length=100, choices=BACK_OFFICE_CHOICES, null=True, blank=True)


    greeting_and_enthusiasm = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)], null=True, blank=True)
    emotional_connection = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(25)], null=True, blank=True)
    resolution_and_professionalism = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(35)], null=True, blank=True)
    hold_procedure = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    call_closure = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)

    zero_rated = models.BooleanField(default=False)

    def __str__(self):
        return f"Outbound - {self.pk}"



class Mapped_employers(models.Model):
    nssf_no = models.CharField(max_length=20)
    employer_name = models.CharField(max_length=300)    
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.nssf_no


class JotFeedback(models.Model):
    nps_rating = models.IntegerField()
    #fcr_resolved = models.BooleanField(null=True, blank=True)
    fcr_resolved = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    ces_easy = models.CharField(max_length=3, null=True, blank=True)
    overall_satisfaction = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    additional_comments = models.TextField(blank=True)
    first_name = models.CharField(max_length=255)  # Corrected
    yourphone = models.CharField(max_length=255)   # Corrected
    csobranch = models.CharField(max_length=255)   # Corrected
    csoname = models.CharField(max_length=255)     # Corrected
    tstamp = models.IntegerField()                 # Corrected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Jotfeedback - {self.pk}"
    



class Suspense(models.Model):
    member_id = models.CharField(max_length=255, null=True, blank=True)
    member_name = models.CharField(max_length=255, null=True, blank=True)
    member_identificat_val = models.CharField(max_length=255, null=True, blank=True)
    submitted_file_name = models.CharField(max_length=255, null=True, blank=True)
    submission_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    init_member_suspense_contr = models.FloatField(null=True, blank=True)
    ident_member_suspense_contr = models.FloatField(null=True, blank=True)
    cur_member_suspense_contr = models.FloatField(null=True, blank=True)
    init_interest_suspense_amount = models.FloatField(null=True, blank=True)
    cur_interest_suspense_amount = models.FloatField(null=True, blank=True)
    ident_interest_suspense = models.FloatField(null=True, blank=True)
    employer_name = models.CharField(max_length=255, null=True, blank=True)
    employer_identificat_val = models.CharField(max_length=255, null=True, blank=True)
    trn = models.CharField(max_length=255, null=True, blank=True)
    receipt_number = models.CharField(max_length=255, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    statutory_ins_detail_id = models.FloatField(null=True, blank=True)
    employerno = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.member_name
