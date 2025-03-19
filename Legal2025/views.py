from django.shortcuts import render,get_object_or_404,redirect
from django.apps import apps  # ✅ Lazy Import
from django.db.models import OuterRef, Subquery,Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LegalFilesForm,LegalFileUpdateForm,LitigationForm,FullyPaidForm, ReconciliationAgreementForm, InstallmentForm, InstallmentUpdateForm,InstallmentUpdateForm, PaymentForm, LegalFileUpdateFormmanager
from .models import LegalFiles,LegalFilesLog, Comment, Attachment,ReconciliationAgreement, Installment ,Payment # Import your models
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings 
from .utils import get_trn_payments, process_trn_in_background
from django.forms import inlineformset_factory
from datetime import datetime
from dateutil import parser  # ✅ Auto-detects date format
import json
import threading
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect



@login_required
def view_legalfiles(request):
    # Subquery to fetch the latest LegalFilesLog status for each LegalFile using created_on
    latest_log = LegalFilesLog.objects.filter(
        legalfile=OuterRef('pk')
    ).order_by('-created_at')

    # Base queryset for all legal files
    legaldata = LegalFiles.objects.all().annotate(
        latest_legal_status=Coalesce(
            Subquery(latest_log.values('legal_status')[:1]), None
        ),
        latest_comment=Coalesce(
            Subquery(latest_log.values('comment')[:1]), None
        )
    ).order_by('-created_on')

    headline = 'All Files in Legal'

    # Latest comments per legal file
    latest_comments = (
        Comment.objects.filter(legal_file__in=legaldata)
        .order_by('legal_file', '-created_on')  # Sort by legal_file, then latest created_on
        .distinct('legal_file')  # Selects only the latest comment per file
    )

    previous_comments = Comment.objects.filter(legal_file__in=legaldata).order_by('-created_on')

    # Filter based on user's group if required
    if request.user.groups.filter(name='Advocates').exists():
        # Fetch cases assigned to or created by the logged-in user
        legaldata = legaldata.filter(
            Q(advocate=request.user) | Q(user=request.user)  # Include both conditions
        )
       
        headline = 'Your Legal Files (Assigned & Created)'

    # Get all users in the "Advocates" group
    advocates_group = Group.objects.get(name="Advocates")
    advocates = User.objects.filter(groups=advocates_group)

    context = {
        'legaldata': legaldata,
        'headline': headline,
        'users': advocates,
        'latest_comments': latest_comments,
        'url_prefix': 'closelegalfile',  # Example prefix for this view
        'button_action': 'Update',  # Example action for the view
    }

    # Determine the template to render based on user's group
    if request.user.groups.filter(name='Advocates').exists():
        return render(request, 'view_legalfiles_Advocates.html', context)
    elif request.user.groups.filter(name='Debt Recovery Manager').exists():
        return render(request, 'view_legalfiles_recovery.html', context)
    elif request.user.groups.filter(name='Legal Managers').exists():
        return render(request, 'view_legalfiles_Managers.html', context)  # Updated for managers
    elif request.user.groups.filter(name='commercial').exists():
        return render(request, 'view_legalfiles_auditor.html', context) 
    else:
        return HttpResponse('Unauthorized', status=401)

# #Add Legal File
@login_required
def legal_file_record(request):
    if request.method == "POST":
        lfm = LegalFilesForm(request.POST, request.FILES)
        if lfm.is_valid():
            legal_file = lfm.save(commit=False)
            legal_file.user = request.user  
            legal_file.save()

            # Process file uploads
            attachments = request.FILES.getlist('attachments')  # Assuming your file input is named 'attachments'
            for attachment in attachments:
                Attachment.objects.create(legal=legal_file, file=attachment)  # Adjust field names as needed

            messages.success(request, 'Successfully Captured Legal File')
            return redirect('legalfiles')  # Redirect to your legal files list view
        else:
            print(lfm.errors)  # Debugging: Print form errors
            messages.add_message(request, messages.ERROR, 'Failed Legal File capture. Please cross-check the entries.')
            return redirect('addfile')  # Redirect to the same page for corrections
    else:
        lfm = LegalFilesForm()

    # Fetch the list of legal files created by the user
    legal_file_data = LegalFiles.objects.filter(user=request.user).order_by('-created_on')  # Assuming `date_created` exists
    return render(request, 'LegalFiles.html', context={'lfm': lfm, 'legal_file_data': legal_file_data})


@login_required
def update_legal_file_advocate(request, id):
    legal_file = get_object_or_404(LegalFiles, id=id)
    advocates_group = Group.objects.get(name="Advocates")  # Defining Advocates Group
    advocates = User.objects.filter(groups=advocates_group)

    if request.method == 'POST':
        form = LegalFileUpdateForm(request.POST, request.FILES)
        litigation_form = LitigationForm(request.POST)
        fully_paid_form = FullyPaidForm(request.POST)

        if form.is_valid():
            comment_text = form.cleaned_data['comment']
            legal_status = form.cleaned_data['legal_status']

            # Create a new comment for this update
            comment = Comment.objects.create(
                legal_file=legal_file,
                created_on=timezone.now(),
                comment=comment_text,
                legal_status=legal_status,
                user=request.user
            )

            # If "Litigation", store court details
            if (legal_status == 'Litigation' or legal_status == "Prosecution") and litigation_form.is_valid():
                comment.court = litigation_form.cleaned_data['court']
                comment.courtfiling_date = litigation_form.cleaned_data['courtfiling_date']
                comment.nexthearing_date = litigation_form.cleaned_data['nexthearing_date']
                comment.save()

                legal_file.court = comment.court
                legal_file.courtfiling_date = comment.courtfiling_date
                legal_file.nexthearing_date = comment.nexthearing_date

                legal_file.save()

            elif legal_status == 'Fully Paid'and fully_paid_form.is_valid():
                comment.amount_paid = fully_paid_form.cleaned_data['amount_paid']
                comment.balance = fully_paid_form.cleaned_data['balance']
                comment.save()

                legal_file.amount_paid = comment.amount_paid
                legal_file.balance = comment.balance
                legal_file.save()

            # Handle file attachments
            attachments = request.FILES.getlist('attachments')
            for attachment in attachments:
                Attachment.objects.create(file=attachment, comment=comment)

            messages.success(request, "Legal file successfully updated.")

            # Redirect to Add Reconciliation Agreement page if selected status is Reconciliation Agreement
            if legal_status == 'Reconciliation Agreement':
                return redirect('add_agreement', legal_file_id=legal_file.id)


            return redirect('update_legalfile', id=legal_file.id)
        else:
            messages.error(request, "Error updating the legal file.")
    else:
        form = LegalFileUpdateForm(initial={'legal_status': legal_file.legal_status})
        litigation_form = LitigationForm()
        fully_paid_form = FullyPaidForm()

    # Get the latest comment and fallback to legal_file data if court details are missing
    latest_comment = legal_file.comments.last()
    court = latest_comment.court if latest_comment and latest_comment.court else legal_file.court
    courtfiling_date = latest_comment.courtfiling_date if latest_comment and latest_comment.courtfiling_date else legal_file.courtfiling_date
    nexthearing_date = latest_comment.nexthearing_date if latest_comment and latest_comment.nexthearing_date else legal_file.nexthearing_date
    previous_comments = Comment.objects.filter(legal_file=legal_file).order_by('-created_on')

    return render(request, 'update_legal_file.html', {
        'form': form,
        'litigation_form': litigation_form,
        'fully_paid_form':fully_paid_form,
        'legal_file': legal_file,
        'previous_comments': previous_comments,
        'court': court,
        'courtfiling_date': courtfiling_date,
        'nexthearing_date':nexthearing_date,
        'advocates': advocates,
    })


@login_required
def add_manager_comment(request, id):
    legal_file = get_object_or_404(LegalFiles, id=id)

    # ✅ Restrict access to users in the "Debt Recovery Manager" group
    if not request.user.groups.filter(name="Debt Recovery Manager").exists():
        messages.error(request, "You do not have permission to add comments.")
        return redirect('dashboard')  # Redirect unauthorized users to the dashboard or another page

    if request.method == 'POST':
        form = LegalFileUpdateFormmanager(request.POST)

        if form.is_valid():
            comment_text = form.cleaned_data['comment']

            # Create a new comment for the legal file
            Comment.objects.create(
                legal_file=legal_file,
                created_on=timezone.now(),
                comment=comment_text,
                user=request.user  # Associate comment with the logged-in manager
            )

            messages.success(request, "Comment successfully added.")
            return redirect('update_legalfile_manager', id=legal_file.id)  # Redirect to legal file details

        else:
            messages.error(request, "Error adding comment.")

    else:
        form = LegalFileUpdateFormmanager()

    # Fetch previous comments for display
    previous_comments = Comment.objects.filter(legal_file=legal_file).order_by('-created_on')

    return render(request, 'add_manager_comment.html', {
        'form': form,
        'legal_file': legal_file,
        'previous_comments': previous_comments
    })


@login_required
def assign_file(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        advocate_id = request.POST.get('advocate')
        
        # Get the legal file and advocate
        legal_file = get_object_or_404(LegalFiles, id=file_id)
        advocate = get_object_or_404(User, id=advocate_id)

        try:
            # Assign the file and update status
            legal_file.forward(user=request.user, advocate=advocate)
            legal_file.save()
            legal_file.refresh_from_db()
            
            # Send notification email to the assigned advocate
            subject = "New Legal File Assigned"
            message = f"Dear {advocate.username},\n\nYou have been assigned a new legal file:\n\n" \
                      f"File Number: {legal_file.nssf_number}\n" \
                      f"Employer: {legal_file.employer_name}\n" \
                      f"Branch: {legal_file.branch}\n" \
                      f"Submitted on: {legal_file.date_received}\n\n" \
                      f"Please Proceed to update the file at your earliest convenience.\n\n" \
                      f"Best Regards,\nNSSF debt recovery Team"
            from_email = settings.DEFAULT_FROM_EMAIL  # Ensure it's set in settings.py
            to_email = advocate.email  

            # Check if the advocate has an email before sending
            if to_email:
                send_mail(subject, message, from_email, [to_email])
                messages.success(
                    request,
                    f"File {legal_file.nssf_number} successfully assigned to {advocate.username} "
                    f"and status updated to {legal_file.case_status}. Notification email sent."
                )
            else:
                messages.warning(
                    request,
                    f"File assigned to {advocate.username}, but no email was sent (email not found)."
                )

        except Exception as e:
            messages.error(request, f"Error updating the file: {e}")
        
        return redirect('files_toassign')
    
    else:
        messages.error(request, "Invalid request method.")
        return redirect('files_toassign')
    

""" Legal files to Assign"""
@login_required
def Legal_Files_to_assign(request):
    #closedata = Forclosure.objects.all() 
    unassigned_files = LegalFiles.objects.filter(case_status='initiated',advocate__isnull=True).order_by('-created_on')
    assigned_files = LegalFiles.objects.filter(case_status='assigned',advocate__isnull=True).order_by('-created_on')
    file_count = unassigned_files.count()
    return render(request, 'files_to_assign.html', context={'unassigned_files': unassigned_files, 'assigned_files':assigned_files, 'entry_count': file_count})



""" Assigned Legal files"""
@login_required
def Assigned_legal_files(request):
    # Subquery to fetch the latest LegalFilesLog status for each LegalFile
    latest_log = LegalFilesLog.objects.filter(
        legalfile=OuterRef('pk')
    ).order_by('-created_at')

    assigned_files = LegalFiles.objects.filter(case_status='assigned').annotate(
        latest_legal_status=Coalesce(
            Subquery(latest_log.values('legal_status')[:1]), None
        )
    ).order_by('-created_on')
   # assigned_files = LegalFiles.objects.filter(case_status='assigned').order_by('-created_on')
    latest_comments = (
        Comment.objects.filter(legal_file__in=assigned_files)
        .order_by('legal_file', '-created_on')
        .distinct('legal_file')
    )

    file_count = assigned_files.count()

    return render(request, 'assigned_files.html', {
        'assigned_files': assigned_files,
        'latest_comments': latest_comments,
        'entry_count': file_count
    })

"""Details of a File in Legal"""
def detail_legalfile(request, id):
    """Retrieve details of a legal file along with related agreements and comments."""
    legal_file = get_object_or_404(LegalFiles, id=id)

    # Fetch related agreements
    related_agreements = ReconciliationAgreement.objects.filter(legal_file=legal_file)

    # Fetch previous comments related to the legal file
    previous_comments = Comment.objects.filter(legal_file=legal_file).order_by('-created_on')

    # Fetch logs for the legal file
    logs = LegalFilesLog.objects.filter(legalfile=legal_file).order_by('-created_at')

    context = {
        'legal_file': legal_file,
        'previous_comments': previous_comments,
        'logs': logs,
        'related_agreements': related_agreements,  # ✅ Include agreements in the context
    }

    return render(request, 'detail_files.html', context)


# Search Legal Files
@login_required
def search_legalfiles(request):
    """
    View to search all legal files based on any field.
    """
    query = request.GET.get('q', '').strip()  # Get query and remove spaces
    headline = "Search All Legal Files"
    search_results = []

    if query:
        print(f"Search Query: {query}")  # Debugging
        search_results = LegalFiles.objects.filter(
            Q(nssf_number__icontains=query) |
            Q(employer_name__icontains=query) 
        )
        print(f"Results Found: {search_results.count()}")  # Debugging
        headline = f"Search Results for '{query}'"

    # Fetch latest comments AFTER search_results is populated
    latest_comments = (
        Comment.objects.filter(legal_file__in=search_results)
        .order_by('legal_file', '-created_on')
        .distinct('legal_file')
    )

    # Define context
    context = {
        'search_results': search_results,
        'latest_comments': latest_comments,
        'headline': headline,
        'query': query,
    }

    return render(request, 'file_search.html', context)



"""Reconciliation Agreements Views"""

"""List all agreements under a specific legal file"""
def agreement_list(request):
    agreements = ReconciliationAgreement.objects.all()
    return render(request, 'agreement_list.html', {'agreements': agreements})

"""Create a new agreement under a legal file"""



def add_agreement(request, legal_file_id):
    legal_file = get_object_or_404(LegalFiles, id=legal_file_id)
    agreement = None  

    if request.method == 'POST':
        form = ReconciliationAgreementForm(request.POST, legal_file=legal_file)  # ✅ Bind form data

        # ✅ Get Handsontable JSON data
        installment_data = request.POST.get("installment_data", "[]")  
        installments = json.loads(installment_data)  

        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.legal_file = legal_file  # ✅ Attach to legal file
            agreement.save()  # ✅ Save agreement first

            valid_installments = []  # ✅ Store valid installment objects
            print(f"✅ Installment Data Received: {installments}")  # Debugging

            for i, installment in enumerate(installments):
                try:
                    if installment["date_of_payment"] and installment["amount"]:  # ✅ Ensure required fields exist
                        date_of_payment = parser.parse(installment["date_of_payment"]).strftime('%Y-%m-%d')  # ✅ Convert to YYYY-MM-DD

                        valid_installments.append(Installment(
                            agreement=agreement,
                            date_of_payment=date_of_payment,
                            amount=installment["amount"],
                            description=installment.get("description", "")
                        ))
                except Exception as e:
                    print(f"⚠ Invalid Date Format in Installment #{i}: {installment['date_of_payment']} - {str(e)}")  # Debugging

            if valid_installments:
                Installment.objects.bulk_create(valid_installments)  # ✅ Bulk insert for efficiency
                print(f"✅ Successfully saved {len(valid_installments)} installments.")

            messages.success(request, "Reconciliation Agreement and Installments saved successfully.")
            return redirect('agreement_list')

        else:
            print("❌ Agreement Form Errors:", form.errors.as_json())  # Debugging
            messages.error(request, "There was an error submitting the form.")

    else:
        form = ReconciliationAgreementForm(legal_file=legal_file)

    return render(request, 'add_agreement.html', {
        'form': form,
        'legal_file': legal_file
    })


def add_installment(request, agreement_id):
    agreement = get_object_or_404(ReconciliationAgreement, id=agreement_id)

    if request.method == 'POST':
        form = InstallmentForm(request.POST)
        
        if form.is_valid():
            installment = form.save(commit=False)
            installment.agreement = agreement  # ✅ Assign to agreement
            installment.save()

            messages.success(request, "Installment successfully added!")
            return redirect('agreement_list')  # ✅ Modify if needed
        else:
            messages.error(request, "Error adding installment.")

    else:
        form = InstallmentForm()

    return render(request, 'add_installment.html', {'form': form, 'agreement': agreement})







"""List of all installments under an Agreement"""
def installment_list(request, agreement_id):
    agreement = get_object_or_404(ReconciliationAgreement, id=agreement_id)
    installments = Installment.objects.filter(agreement=agreement)  # Get only related installments
    return render(request, 'view_installments.html', {'installments': installments, 'agreement': agreement})

"""View Installment Details"""
def installment_detail(request, installment_id):
    installment = get_object_or_404(Installment, id=installment_id)
    payments = installment.payments.all()  # Get all payments related to this installment

    return render(request, 'installment_detail.html', {
        'installment': installment,
        'payments': payments,
    })


def edit_installment(request, installment_id):
    """Handles editing an installment & validating TRN before saving."""
    installment = get_object_or_404(Installment, id=installment_id)
    legal_file = installment.agreement.legal_file

    if request.method == "POST":
        trn = request.POST.get("transaction_reference_number", "").strip().upper()

        if trn:
            # ✅ Check if TRN has already been recorded
            if Payment.objects.filter(
                installment__agreement__legal_file=legal_file,
                transaction_reference_number=trn
            ).exists():
                messages.error(request, "This TRN has already been captured for another installment.")
                return redirect("update_installment", installment_id=installment.id)

            # ✅ Fetch TRN payment details
            trn_data = get_trn_payments(
                legal_file.nssf_number, trn,
                legal_file.audited_period_startdate.strftime('%d-%m-%Y'),
                legal_file.audited_period_enddate.strftime('%d-%m-%Y')
            )

            total_payment = trn_data.get("total_payment", 0)
            payment_date = trn_data.get("payment_date")

            # ✅ Ensure payment_date is properly formatted
            if not payment_date or payment_date == "N/A":
                payment_date = "N/A"

            # ✅ If TRN does not match company or is outside scope, show error
            if total_payment == 0:
                messages.error(request, "TRN paid period is outside audited scope or does not belong to this company.")
                return redirect("update_installment", installment_id=installment.id)

            # ✅ Save TRN and trigger background processing
            installment.transaction_reference_number = trn
            installment.save(update_fields=['transaction_reference_number'])

            threading.Thread(target=process_trn_in_background, args=(installment, trn, legal_file)).start()
            
            messages.success(request, f"TRN {trn} saved. Reconciliation will happen in the background.")

            # ✅ Redirect user back to previous page
            referer = request.META.get('HTTP_REFERER', None)
            if referer:
                return HttpResponseRedirect(referer)
            return redirect("update_installment", installment_id=installment.id)

    return render(request, "edit_installment.html", {"installment": installment})


def check_trn_payment_status(request, trn, legal_file_id):
    """Check TRN payments and return total amount, payment date, and warnings."""
    legal_file = get_object_or_404(LegalFiles, id=legal_file_id)

    # Get the correct company's NSSF number (from the legal file)
    company_nssf_number = legal_file.nssf_number  
    trn = trn.strip().upper()
    

    # Check if TRN has already been captured for any installment in this agreement
    existing_payment = Payment.objects.filter(
        installment__agreement__legal_file=legal_file,
        transaction_reference_number=trn
    ).exists()

    if existing_payment:
        return JsonResponse({
            "trn": trn,
            "legal_file": legal_file_id,
            "error": "This TRN has already been captured for another installment in this agreement.",
            "total_payment": 0,
            "payment_date": "N/A"
        })

    # Fetch total payment, latest payment date, and queried NSSF number for this TRN
    
    # trn_data = get_trn_payments(trn, legal_file.audited_period_startdate, legal_file.audited_period_enddate, company_nssf_number)
    # trn_data = get_trn_payments(company_nssf_number, trn, legal_file.audited_period_startdate, legal_file.audited_period_enddate)
    trn_data = get_trn_payments(
    company_nssf_number, trn, 
    legal_file.audited_period_startdate.strftime('%d-%m-%Y'), 
    legal_file.audited_period_enddate.strftime('%d-%m-%Y')
)


    total_payment = trn_data.get("total_payment", 0)
    payment_date = trn_data.get("payment_date")
    print("✅ TRN Data Retrieved:", trn_data)

    # Ensure `payment_date` is properly formatted
    if not payment_date or payment_date == "N/A":
        payment_date = "N/A"

    # If no payment was found, return the appropriate message
    if total_payment == 0:
        return JsonResponse({
            "trn": trn,
            "legal_file": legal_file_id,
            "total_payment": 0,
            "payment_date": "N/A",
            "message": "TRN paid period is outside audited scope or does not belong to this company."
        })

    return JsonResponse({
        "trn": trn,
        "legal_file": legal_file_id,
        "total_payment": total_payment,
        "payment_date": payment_date,
        "message": ""
    })


"""Court Dates Calendar"""
def calendar_view(request):
    events = []

    # Get all legal files with hearing dates
    legal_files = LegalFiles.objects.prefetch_related('comments')

    for file in legal_files:
        # ✅ First, check if LegalFiles has nexthearing_date
        if file.nexthearing_date:
            print(f"DEBUG: Using nexthearing_date from LegalFiles -> {file.employer_name}: {file.nexthearing_date}")
            events.append({
                "title": file.employer_name,
                "court": file.court,
                "advocate": file.advocate.get_full_name(),
                "start": file.nexthearing_date.strftime('%Y-%m-%d'),  # Correct format
                "url": f"/details_offiles/{file.id}/",
                "color": "orange"
            })
            continue  # Skip fetching from comments if already found

        # ✅ If not found in LegalFiles, check the latest Comment
        latest_comment = file.comments.filter(nexthearing_date__isnull=False).order_by('-created_on').first()

        if latest_comment:
            print(f"DEBUG: Using nexthearing_date from Comment -> {file.employer_name}: {latest_comment.nexthearing_date}")
            events.append({
                "title": file.employer_name,
                "start": latest_comment.nexthearing_date.strftime('%Y-%m-%d'),
                "url": f"/details_offiles/{file.id}/",
            })

    print(f"Final Events JSON: {events}")  # ✅ Debugging output

    context = {
        "events": events
    }

    return render(request, "calendar.html", context)
