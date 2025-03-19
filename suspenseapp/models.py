from django.db import models

# Create your models here.

class Suspense(models.Model):
    member_id = models.CharField(max_length=255, null=True, blank=True)
    member_name = models.CharField(max_length=255, null=True, blank=True)
    member_identificat_val = models.CharField(max_length=255, null=True, blank=True)
    submitted_file_name = models.CharField(max_length=255, null=True, blank=True)
    submission_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
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
    

class FundTins(models.Model):
    employerno = models.CharField(max_length=50, unique=True, verbose_name="Employer Number")
    employer_name = models.CharField(max_length=255, verbose_name="Employer Name")
    tin = models.CharField(max_length=20, verbose_name="TIN")  # Store as CharField to handle leading zeros
    name_from_ura = models.CharField(max_length=255, verbose_name="Name from URA")
    matching_percentage = models.IntegerField(verbose_name="Matching Percentage")
    source_of_tin = models.CharField(max_length=50, verbose_name="Source of TIN")

    class Meta:
        verbose_name = "Fund TIN"
        verbose_name_plural = "Fund TINs"
        ordering = ["employerno"]  # Orders results by Employer Number

    def __str__(self):
        return f"{self.employerno} - {self.employer_name} ({self.tin})"

    
class SuspenseSummary(models.Model):
    employerno = models.CharField(max_length=255, null=True, blank=True)
    employer_name = models.CharField(max_length=255, null=True, blank=True)
    total_suspense_contr = models.FloatField(null=True, blank=True)
    records_count = models.IntegerField(null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    scope_months = models.IntegerField(null=True, blank=True)

    tin = models.ForeignKey(FundTins, on_delete=models.SET_NULL, null=True, blank=True, related_name="suspense_summaries")

    class Meta:
        verbose_name = "Suspense Summary"
        verbose_name_plural = "Suspense Summaries"

    def __str__(self):
        return f"{self.employer_name} - {self.employerno}"




class URA_tins(models.Model):
    taxpayer_name = models.TextField(null=True, blank=True)
    trading_name = models.TextField(null=True, blank=True)
    business_name = models.TextField(null=True, blank=True)
    taxpayer_id = models.TextField(unique=True)  # Taxpayer Identification Number (TIN)
    business_start_date = models.TextField(null=True, blank=True)  # Changed from DateField to TextField
    registration_status = models.TextField(null=True, blank=True)
    
    # Contact Details
    landline_number = models.TextField(null=True, blank=True)
    mobile_number = models.TextField(null=True, blank=True)
    
    # Business Information
    current_sector_main_activity = models.TextField(null=True, blank=True)
    taxpayer_type = models.TextField(null=True, blank=True)
    
    # Contact Person
    contact_name = models.TextField(null=True, blank=True)
    contact_person_designation = models.TextField(null=True, blank=True)
    contact_person_email = models.TextField(null=True, blank=True)  # Changed from EmailField to TextField
    contact_person_landline = models.TextField(null=True, blank=True)
    contact_person_mobile = models.TextField(null=True, blank=True)
    
    # Business Certificates
    business_certificate_id = models.TextField(null=True, blank=True)
    certificate_of_incorporation_id = models.TextField(null=True, blank=True)
    
    # Business Address
    business_district = models.TextField(null=True, blank=True)
    business_building_name = models.TextField(null=True, blank=True)
    business_country = models.TextField(null=True, blank=True)
    business_plot_number = models.TextField(null=True, blank=True)
    business_street_address = models.TextField(null=True, blank=True)
    business_sub_country = models.TextField(null=True, blank=True)
    business_trade_center = models.TextField(null=True, blank=True)
    business_village = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.taxpayer_name} ({self.taxpayer_id})"



class EmploymentHistory(models.Model):
    member_number = models.TextField(null=True, blank=True, verbose_name="Member Number")
    member_name = models.TextField(null=True, blank=True, verbose_name="Member Name")
    employer_name = models.TextField(null=True, blank=True, verbose_name="Employer Name")
    start_year = models.TextField(null=True, blank=True, verbose_name="Start Year")
    end_year = models.TextField(null=True, blank=True, verbose_name="End Year")  # Allows NULL for Current Employers
    category = models.TextField(null=True, blank=True, verbose_name="Category")

    class Meta:
        verbose_name = "Employment History"
        verbose_name_plural = "Employment Histories"

    def __str__(self):
        return f"{self.member_number} - {self.employer_name} ({self.category})"


class SuspenseLeads(models.Model):
    member_name = models.CharField(max_length=255, null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    #end_date = models.CharField(max_length=255, null=False, blank=False)  # If date, use models.DateField()
    init_member_suspense_contr = models.FloatField(null=False, blank=False)
    employer_name = models.CharField(max_length=255, null=False, blank=False)
    employerno = models.CharField(max_length=255, null=False, blank=False)
    member_month_year_s = models.CharField(max_length=255, null=False, blank=False)
    employeename = models.CharField(max_length=255, null=False, blank=False)
    employeetin = models.BigIntegerField(null=False, blank=False)
    employeetodt = models.DateField(null=False, blank=False)
    #employeetodt = models.CharField(max_length=255, null=False, blank=False)  # Consider DateField if necessary
    basicsalary = models.FloatField(null=False, blank=False)
    grosstotincome = models.FloatField(null=False, blank=False)
    member_month_year = models.CharField(max_length=255, null=False, blank=False)
    ura_based_nssf = models.FloatField(null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(max_length=255, null=False, blank=False)
    contact = models.CharField(max_length=255, null=False, blank=False)
    new_name = models.CharField(max_length=255, null=False, blank=False)
    percentage_match = models.FloatField(null=False, blank=False)
    num_best_matches = models.IntegerField(null=False, blank=False)
    mobile = models.CharField(max_length=255, null=False, blank=False)
    nssfno_by_phone = models.CharField(max_length=255, null=True, blank=True)
    nssfno_by_email = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.member_name} - {self.employer_name}"



