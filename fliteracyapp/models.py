from django.contrib.auth.models import Group, User
from django.db import models
from multiselectfield import MultiSelectField

def get_default_attachment():
    # Provide the path to the default attachment
    return 'attachments/default_file.pdf'


#User = get_user_model()



class Nssfmember(models.Model):
    name = models.CharField(max_length=200)
    nssf_number = models.CharField(max_length=50)
    employer = models.CharField(max_length=200)
    employer_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=300)
    email = models.EmailField()
    date_of_birth = models.DateField()
    mothers_name = models.CharField(max_length=200)
    fathers_name = models.CharField(max_length=200)

    def __str__(self):
        return self.name




class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    #forclosure = models.ForeignKey('Forclosure', on_delete=models.CASCADE, related_name='attachments')
    fl_event = models.ForeignKey('Fl_event', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)



class Fl_event(models.Model):
    PROGRAM_CHOICES = [
        ('Money Talk', 'Money Talk'),
        ('Townhall', 'Townhall'),
        ('Webinar', 'Webinar'),
    ]

    DELIVERY_MODE_CHOICES = [
        ('Physical', 'Physical'),
        ('Online', 'Online'),
        ('Hybrid', 'Hybrid'),
    ]

    advisor_choices = [
        ('Anna Maria Sanyu', 'Anna Maria Sanyu'),
        ('Aisha Nakanwagi', 'Aisha Nakanwagi'),
        ('Jackline Nagasha', 'Jackline Nagasha'),
        ('Appolo Mbowa Kibirango', 'Appolo Mbowa Kibirango')]

    event_name = models.CharField(max_length=100)
    event_date = models.DateField()
    employer = models.CharField(max_length=100, blank=True, null=True)
    employer_number = models.CharField(max_length=100, blank=True, null=True)
    #fl_advisors_involved = models.CharField(max_length=100, blank=True, null=True)  # This could be a MultipleChoiceField in a form
    
    fl_advisors_involved = MultiSelectField(choices=advisor_choices, blank=True, null=True)
    
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    contact_phone = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    program = models.CharField(max_length=100, choices=PROGRAM_CHOICES, blank=True, null=True)
    delivery_mode = models.CharField(max_length=100, choices=DELIVERY_MODE_CHOICES, blank=True, null=True)
    rms_involved = models.ManyToManyField(User, limit_choices_to={'groups__name': 'Officers'}, blank=True)
    on_spot_feedback = models.BooleanField(default=False)


class Fl_attendants(models.Model):
    name = models.CharField(max_length=100)
    nssf_number = models.CharField(max_length=20)
    event_name = models.CharField(max_length=100)
    event_date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.event_name} - {self.event_date}"
    



