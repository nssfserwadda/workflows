from django.db import models

# Create your models here.

class Feedback(models.Model):
    feedback_type = models.CharField(max_length=255)
    rating = models.IntegerField()

    def __str__(self):
        return f"{self.feedback_type} - {self.rating}"
    
class JotFeedback(models.Model):
    nps_rating = models.IntegerField()
    fcr_resolved = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    ces_easy = models.CharField(max_length=3, null=True, blank=True)
    overall_satisfaction = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    additional_comments = models.TextField(blank=True)
    first_name = models.CharField(max_length=255,null=True, blank=True)  # Corrected
    yourphone = models.CharField(max_length=255,null=True, blank=True)   # Corrected
    csobranch = models.CharField(max_length=255,null=True, blank=True)   # Corrected
    csoname = models.CharField(max_length=255,null=True, blank=True)     # Corrected
    tstamp = models.CharField(max_length=255,null=True, blank=True)     # Corrected

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Jotfeedback - {self.pk}"