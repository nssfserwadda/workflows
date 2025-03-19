from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django_fsm import transition, FSMIntegerField, FSMField, transition
from django_fsm_log.decorators import fsm_log_by, fsm_log_description
from .utils import get_trn_payments
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import process_trn_in_background  # ✅ Correct Import

# from .views import process_trn_in_background
import threading


class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    #forclosure = models.ForeignKey('Forclosure', on_delete=models.CASCADE, related_name='attachments')
    legal= models.ForeignKey('LegalFiles', on_delete=models.CASCADE, related_name='legal_attachments',blank=True, null=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='comment_attachments',blank=True, null=True)

    #generalquery = models.ForeignKey('Generalquery', on_delete=models.CASCADE, related_name='attachments',blank=True, null=True)

#Files submitted to Legal
class LegalFiles(models.Model):
    LEGAL_STATUS_CHOICES = [
        ('Compliance engagement', 'Compliance engagement'),
        ('Consent Judgement', 'Consent Judgement'),
        ('Deed of settlement', 'Deed of settlement'),
        ('Deed signed. Pending confirmation of fully paid', 'Deed signed. Pending confirmation of fully paid'),
        ('Employer Closed', 'Employer Closed'),
        ('Execution', 'Execution'),
        ('Fully Paid', 'Fully Paid'),
        ('Litigation', 'Litigation'),
        ('Negotiation', 'Negotiation'),
        ('Notice of Intention to sue', 'Notice of Intention to sue'),
        ('Notice of Motion', 'Notice of Motion'),
        ('Orders issued', 'Orders issued'),
        ('Penalty waiver', 'Penalty waiver'),
        ('Plea Bargaining Agreement', 'Plea Bargaining Agreement'),
        ('Prosecution /Warrant', 'Prosecution /Warrant'),
        ('Prosecution', 'Prosecution'),
        ('Reconciliation Agreement', 'Reconciliation Agreement'),
        ('Returned to Compliance', 'Returned to Compliance'),
        ('Under receivership', 'Under receivership'),
    ]

    SOURCE_CHOICES = [
        ('Legacy', 'Legacy'),
        ('Current', 'Current'),
    ]
    STATUS_CHOICES = [
        ('initiated', 'initiated'),
        ('assigned', 'assigned'),
        ('updated', 'updated'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='legalfiles', default=1)
    fy_submitted_to_legal = models.CharField(max_length=10, null=True, blank=True)  
    fy_deed_signed = models.CharField(max_length=10, null=True, blank=True)  
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES,null=True, blank=True )
    case_status = FSMField(default='initiated',choices=STATUS_CHOICES, null=True, blank=True)
    legal_status = models.CharField(max_length=50, choices=LEGAL_STATUS_CHOICES, null=True, blank=True)
    employer_name = models.CharField(max_length=255,null=True, blank=True)
    nssf_number = models.CharField(max_length=50,null=True, blank=True)
    # advocate = models.CharField(max_length=255, null=True, blank=True)
    advocate = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_cases')
    auditor = models.CharField(max_length=255,null=True, blank=True)
    branch = models.CharField(max_length=255,null=True, blank=True)
    audited_period_startdate = models.DateField(null=True, blank=True)
    audited_period_enddate = models.DateField(null=True, blank=True)
    total_arrears = models.DecimalField(max_digits=20, decimal_places=2,null=True, blank=True)
    special_contribution = models.DecimalField(max_digits=20, decimal_places=2,null=True, blank=True)
    interest = models.DecimalField(max_digits=20, decimal_places=2,null=True, blank=True)
    penalties = models.DecimalField(max_digits=20, decimal_places=2,null=True, blank=True)
    ten_percent_penalty = models.DecimalField(max_digits=20, decimal_places=2,null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    date_received = models.DateField(null=True, blank=True)
    detailed_status = models.TextField(null=True, blank=True)
    court = models.CharField(max_length=255,null=True, blank=True)
    courtfiling_date = models.DateField(null=True, blank=True)
    nexthearing_date = models.DateField(null=True, blank=True)
    closure_date = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employer_name} - {self.legal_status}"
    
    @fsm_log_by
    @fsm_log_description
    @transition(field=case_status, source='initiated', target='assigned')
    def forward(self,user, advocate):
        #self.remark = remark
        print(f"Transitioning {self} to 'assigned'")
        self.advocate = advocate
        self.save()
        print(f"Saved {self}. New status: {self.case_status}")
        LegalFilesLog.objects.create(legalfile=self, user=user, action='forward')
        #pass
        

    @fsm_log_by
    @fsm_log_description
    @transition(field=case_status, source='assigned', target='updated')
    def cancel(self,user):
        #self.remark = remark
        self.save()
        LegalFilesLog.objects.create(legalfile=self, user=user, action='approve')
        #pass

    def get_current_legal_status(self):
        """Retrieve the latest legal status from comments if available, otherwise return the stored legal status."""
        latest_comment = self.comments.order_by('-created_on').first()
        if latest_comment and latest_comment.legal_status:
            return latest_comment.legal_status
        return self.legal_status  # Return the initially imported status if no comments exist

        #pass
#files in Legal Logs
class LegalFilesLog(models.Model):
    legalfile = models.ForeignKey(LegalFiles, on_delete=models.CASCADE, related_name='legallogs')  # Add this field
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    legal_status = models.CharField(max_length=255,blank=True, null=True)
    action = models.CharField(max_length=255,blank=True, null=True)


#Comments added to a legal file
class Comment(models.Model):
    legal_file = models.ForeignKey(LegalFiles, on_delete=models.CASCADE, related_name='comments', default=1)  # Use legal_file as the field name
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50)
    legal_status = models.CharField(max_length=50,null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='legal2025_comments')
    court = models.CharField(max_length=255, null=True, blank=True)
    courtfiling_date = models.DateField(null=True, blank=True)
    nexthearing_date = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"Comment by {self.user.username} on {self.date_added}"
    

"""Models for Reconciliation Agreements"""
class ReconciliationAgreement(models.Model):
    legal_file = models.ForeignKey(LegalFiles, on_delete=models.CASCADE, related_name="agreements")
    total_arrears = models.DecimalField(max_digits=20,decimal_places=2)
    total_interest = models.DecimalField(max_digits=20,decimal_places=2)
    penalty_10percent = models.DecimalField(max_digits=20,decimal_places=2)
    # audited_period_startdate = models.DateField()
    # audited_period_enddate = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def total_expected_amount(self):
        """Calculates the total expected payment from all installments"""
        return sum(self.installments.values_list('amount', flat=True))
        

    def total_paid_amount(self):
        """Calculates the sum of all paid installments whose status is paid"""
        return sum(self.installments.filter(status='PAID').values_list('amount', flat=True))
        # return self.installments.get_total_paid()
    
    def payment_progress(self):
        """Calculates the percentage of the agreement that has been paid"""
        expected = self.total_expected_amount()
        paid = self.total_paid_amount()
        return (paid / expected) * 100 if expected > 0 else 0

    def __str__(self):
        return f"Agreement {self.legal_file.nssf_number} (File {self.legal_file.nssf_number})"

"""Agreement Installments Model"""
class Installment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
    ]

    agreement = models.ForeignKey(ReconciliationAgreement, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField(null=True, blank=True)
    transaction_reference_number = models.CharField(max_length=50, null=True, blank=True)  # ✅ Store TRN
    custom_id = models.PositiveIntegerField(editable=False, null=True, blank=True)
    date_of_payment = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', editable=False)

    def get_total_paid(self):
        """Calculate total amount paid from all related payments."""
        total = self.payments.aggregate(total_paid=Sum('amount_paid'))['total_paid']
        return total if total else 0

    def get_pending_balance(self):
        """Calculate remaining balance to be paid."""
        return max(self.amount - self.get_total_paid(), 0)

    def update_status(self):
        """Automatically update amount_paid, balance, and status based on payments."""
        self.amount_paid = self.get_total_paid()
        self.balance = self.get_pending_balance()

        # ✅ Allow status to remain PENDING even with a TRN
        if self.amount_paid == 0:
            self.status = 'PENDING'
        elif self.amount_paid < self.amount:
            self.status = 'PARTIALLY_PAID'
        else:
            self.status = 'PAID'

        self.save(update_fields=['amount_paid', 'balance', 'status', 'transaction_reference_number'])


class Payment(models.Model):
    agreement = models.ForeignKey(ReconciliationAgreement, null=True, blank=True, on_delete=models.CASCADE, related_name="payments")
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE, related_name="payments")
    transaction_reference_number = models.CharField(max_length=50, unique=True)  # Prevent duplicate TRNs
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    payment_date = models.DateField()

    def save(self, *args, **kwargs):
        """Fetch TRN details, validate, and save payment to database."""

        print(f"🔍 DEBUG: Attempting to save payment for TRN: {self.transaction_reference_number}")

        # Ensure TRN is uppercase and trimmed
        self.transaction_reference_number = self.transaction_reference_number.strip().upper()

        # Fetch TRN payment details
        trn_data = get_trn_payments(
            self.installment.agreement.legal_file.nssf_number, 
            self.transaction_reference_number, 
            self.installment.agreement.legal_file.audited_period_startdate.strftime('%d-%m-%Y'), 
            self.installment.agreement.legal_file.audited_period_enddate.strftime('%d-%m-%Y')
        )

        print(f"✅ DEBUG: TRN Data Retrieved: {trn_data}")

        # Check if payment exists for this TRN
        if trn_data and "total_payment" in trn_data:
            self.amount_paid = trn_data["total_payment"]
            self.payment_date = trn_data.get("payment_date", None)
        else:
            print("⚠ WARNING: No valid payment found for TRN. Defaulting to 0.")
            self.amount_paid = 0  # Ensure amount is still saved

        # Save the Payment first
        super().save(*args, **kwargs)

        # Update the Installment status immediately after saving
        self.installment.update_status()
        self.installment.save()

        print(f"✅ DEBUG: Payment {self.transaction_reference_number} saved successfully with amount {self.amount_paid}.")


"""Calendar Event"""
class HearingEvent(models.Model):
    legal_file = models.ForeignKey(LegalFiles, on_delete=models.CASCADE, related_name='hearings')
    nexthearing_date = models.DateField()
    description = models.TextField()
    
    def __str__(self):
        return f"{self.legal_file.employer_name} - {self.nexthearing_date}"


@receiver(post_save, sender=Installment)
def auto_reconcile_installment(sender, instance, **kwargs):
    """Automatically reconcile TRN when an installment is saved"""
    if instance.transaction_reference_number:
        legal_file = instance.agreement.legal_file
        threading.Thread(target=process_trn_in_background, args=(instance, instance.transaction_reference_number, legal_file)).start()
