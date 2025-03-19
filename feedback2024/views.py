# your_app_name/views.py
from django.utils import timezone  # Add this import statement
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from .forms import WhistleblowerUpdateForm, WhistleblowerClosureForm, WhistleblowerReviewForm
from .models import Whistleblower, Comment, WhistleblowerLog, Attachment
from django.http import HttpResponseRedirect
import requests
import base64
import json
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from django.contrib import messages  # Import messages
from datetime import datetime
from django.db.models import Q, OuterRef, Subquery

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.http import JsonResponse

import smtplib

from .forms import (
    BaseProfilingForm,
    StatementQueryForm, 
    EmployerNotRegisteredForm, 
    EmployerRegisteredMemberKnownForm,
    EmployerRegisteredMemberAnonymousForm
)

# Email configuration
sender_email = 'nssfbiu@nssfug.org'
password = '2X^te8U4Gb64F8e!'
smtp_server = 'webmail.nssfug.org'
smtp_port = 587

#@login_required
"""
def view_wbcases(request):
    wbdata = Whistleblower.objects.all().order_by('-date_submitted')    
    return render(request, 'view_wbcases.html', context={'wbdata': wbdata})

"""

def view_wbcases(request):
    # Subquery to fetch the latest WhistleblowerLog status for each whistleblower
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')
    ).order_by('-created_at')

    # Base queryset for all whistleblower cases
    wbdata = Whistleblower.objects.all().annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),
            None
        ),
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest review_status
            None
        )
    ).order_by('-date_submitted')

    headline = 'All whistleblower cases'

    # Check if the user belongs to the 'Auditors' group
    if request.user.groups.filter(name='Auditors').exists():
        # Filter the cases where bi_auditor_user_id matches the current user's ID
        wbdata = wbdata.filter(bi_auditor_user_id=str(request.user.id))
        headline = 'Whistleblower cases assigned to you'

    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'closewb',  # Example prefix for this view
        'button_action': 'Update',  # Example prefix for this view        
        
    }


    # Determine which template to render based on the user's group
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)
    else:
        return HttpResponse('Unauthorized', status=401)


def is_valid_phone_number(contact):
    """Basic phone number validation, including empty check."""
    if not contact:  # Check if the contact field is empty
        return False
    
    phone_pattern = re.compile(r'^\+?\d{10,15}$')  # Matches international phone numbers
    return bool(phone_pattern.match(contact))

    #return render(request, 'view_wbcases.html', context={'wbdata': wbdata})

def closed_by_auditor_cases(request):
    # Filter cases with the status 'Closed by auditor'
    cases = Whistleblower.objects.filter(status='Closed by auditor').order_by('-created_at')
    
    # Pass the cases to the template
    return render(request, 'closed_cases.html', {'cases': cases})

def send_email(contact_email, message, subject):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = contact_email
        msg['Subject'] = subject

        # Attach the email body
        msg.attach(MIMEText(message, 'plain'))

        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, contact_email, msg.as_string())

        # Close the connection
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False




def send_sms(contact, message):
    url = "https://eservices.nssfug.org/smsnssf/sendsms.php"
    userAndPass = base64.b64encode(b"cso:4t7gcQWaUDYdeGEGdnoj0mXLA").decode("ascii")
    
    payload = json.dumps({
        "destination": "\"" + contact + "\"",
        "content": message
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + userAndPass
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending SMS: {e}, Response: {response.text}")
        return str(e)



def success_view(request):
    return HttpResponse("Report successfully created.")



def edit_whistleblower(request, pk):
    whistleblower = get_object_or_404(Whistleblower, pk=pk)
    comments = Comment.objects.filter(key=whistleblower.key).order_by('-date_added')
        # Get the latest WhistleblowerLog entry for the whistleblower
    latest_log = WhistleblowerLog.objects.filter(whistleblower=whistleblower).order_by('-created_at').first()

    # Initialize the form variable
    form = WhistleblowerUpdateForm(instance=whistleblower)


    if request.method == 'POST':
        if 'update' in request.POST:
            form = WhistleblowerUpdateForm(request.POST, instance=whistleblower)
            if form.is_valid():
                form.save()
                #return redirect('sucs')
                messages.success(request, "Whistleblower information updated successfully.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
            else:                
                #return JsonResponse({"status": "error", "message": f"There was an error updating the whistleblower information. Please check the form."})
                messages.error(request, "There was an error updating the whistleblower information. Please check the form.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
        
        elif 'send_sms' in request.POST:
            message = request.POST.get('sms_message', '')
            contact = whistleblower.updated_member_contact
            if is_valid_phone_number(contact):
                sms_result = send_sms(contact, message)

                if sms_result is True:
                    Comment.objects.create(
                        key=whistleblower.key,
                        comment=message,
                        from_user_id=request.user.id,
                        date_added=timezone.now(),
                        comment_mode='SMS',
                        receiver_phone=contact,
                        user_id=request.user.id,
                    )
                    #return JsonResponse({"status": "success", "message": "SMS sent successfully."})
                    messages.success(request, "SMS sent successfully.")
                else:
                    #return JsonResponse({"status": "error", "message": f"Error sending message: {sms_result}"})
                    messages.error(request, "Error sending SMS.")
                
            else:
                
                #return JsonResponse({"status": "error", "message": f"Invalid Phone Number: {contact}"})
                messages.error(request, "Invalid Phone Number")
                            
                #return redirect('engag')
                return redirect(request.META.get('HTTP_REFERER', '/'))

            
        elif 'send_email' in request.POST:
            message = request.POST.get('email_message', '')
            contact_email = whistleblower.updated_member_email
            subject = 'NSSF Whistleblower Update'
            email_result = send_email(contact_email, message, subject)
            
            if email_result is True:
                Comment.objects.create(
                    key=whistleblower.key,
                    comment=message,
                    from_user_id=request.user.id,
                    date_added=timezone.now(),
                    comment_mode='Email',
                    receiver_email=contact_email,
                    user_id=request.user.id,
                )
                #return JsonResponse({"status": "success", "message": "Email sent successfully."})
                messages.success(request, "Email sent successfully.")
            else:
                #return JsonResponse({"status": "error", "message": f"Error sending message: {email_result}"})
                messages.error(request, "Error sending message")
                            
                #return redirect('engag')
                return redirect(request.META.get('HTTP_REFERER', '/'))

    else:
        form = WhistleblowerUpdateForm(instance=whistleblower)

    context = {
        'form': form,
        'whistleblower': whistleblower,
        'comments': comments,
        'latest_status': latest_log.status if latest_log else whistleblower.status,  # Add the latest status to the context
        'other_details': {
            'key': whistleblower.key,
            'nssf_number': whistleblower.nssf_number,
            'type': whistleblower.type,
            'company_number': whistleblower.company_number,
            'company_name': whistleblower.company_name,
            'created_on': whistleblower.created_on,
            'short_title': whistleblower.short_title,
            'description': whistleblower.description,
            'other_info': whistleblower.other_info,
            'status': whistleblower.status,
            'auditor_name': whistleblower.auditor_name,
        }
    }
    
    return render(request, 'case_communications.html', context)




@login_required
def close_by_auditor(request, pk):
    whistleblower = get_object_or_404(Whistleblower, pk=pk)
        # Get the latest WhistleblowerLog entry for the whistleblower
    latest_log = WhistleblowerLog.objects.filter(whistleblower=whistleblower).order_by('-created_at').first()
    #review_status1=latest_log.review_status

    if request.method == 'POST': 
        form = WhistleblowerClosureForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            # Save the closure log with status update
            comment1 = form.cleaned_data['comment']
            status1 = form.cleaned_data['status']
            whistleblowerLog = WhistleblowerLog.objects.create(
                key=whistleblower.key,
                created_at=timezone.now(),
                comment=comment1,
                #status='Closed by auditor',

                status = status1,
                review_status='Pending',
                confirmed_status='Pending',
                user=request.user,  # Assign the current user directly
                whistleblower=whistleblower  # Assign the whistleblower instance
            )
            

            # Handle file attachments if any
            attachments = request.FILES.getlist('attachments')
            for attachment in attachments:
                Attachment.objects.create(file=attachment, whistleblowerLog=whistleblowerLog)

            
            messages.success(request, "Closure case submitted successifully")

            #return redirect('sucs')  # Redirect to a success page
            return redirect(request.META.get('HTTP_REFERER', '/'))

        else:
            return HttpResponse("Error updating closure.")

    form = WhistleblowerClosureForm()


    return render(request, 'close_whistleblower22.html', {
        'form': form, 
        'whistleblower': whistleblower,
        'latest_status': latest_log.status if latest_log else whistleblower.status,
        'confirmed_status2': latest_log.confirmed_status if latest_log else 'Pending',
        'review_status2': latest_log.review_status if latest_log else 'Pending',
        'comment2': latest_log.comment if latest_log else '',
    })

@login_required
def review_closure(request, pk):
    # Get the specific WhistleblowerLog entry being reviewed
    whistleblower = get_object_or_404(Whistleblower, pk=pk)
    
    # Get the WhistleblowerLog entries related to the whistleblower
    whistleblower_logs = WhistleblowerLog.objects.filter(whistleblower=whistleblower)
    
    # Retrieve attachments related to the logs of the whistleblower
    attachments = Attachment.objects.filter(whistleblowerLog__in=whistleblower_logs)

    whistleblower_log = None  # Initialize whistleblower_log

    # Get the latest WhistleblowerLog entry for the whistleblower
    latest_log = WhistleblowerLog.objects.filter(whistleblower=whistleblower).order_by('-created_at').first()
    stage = latest_log.status if latest_log else whistleblower.status
    #confirmed_status2 = latest_log.confirmed_status if latest_log else None

   

    if request.method == 'POST':
        form = WhistleblowerReviewForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            comment1 = form.cleaned_data['comment']

            # Update the status based on the reviewer's decision
            if decision == 'confirmed':
                
                review_status1 = 'Status confirmed'
                confirmed_status1 = stage
            elif decision == 'disputed':
                
                review_status1 = 'Status disputed'
                confirmed_status1 = None

            whistleblower_log = WhistleblowerLog.objects.create(
                key=whistleblower.key,
                created_at=timezone.now(),
                comment=comment1,
                review_status=review_status1,
                confirmed_status=confirmed_status1,
                status=stage,
                
                user=request.user,  # Assign the current user directly
                whistleblower=whistleblower  # Assign the whistleblower instance
            )
            messages.success(request, "Closure case review submitted successifully")

            #return redirect('sucs')  # Redirect to a success page
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = WhistleblowerReviewForm()

    # Pass whistleblower_log only if it has been created
    context = {
        'form': form,
        'whistleblower_log': whistleblower_log if whistleblower_log else whistleblower,
        'whistleblower': whistleblower,
        'attachments': attachments, # Pass the retrieved attachments to the template
        'latest_status': latest_log.status if latest_log else whistleblower.status,  # Add the latest status to the context
        'confirmed_status2': latest_log.confirmed_status if latest_log else None,
        'review_status2': latest_log.review_status if latest_log else 'Pending review',
        'comment2': latest_log.comment if latest_log else '',
    }

    return render(request, 'review_closure22.html', context)

@login_required
def case_profiling(request, pk):
    whistleblower = get_object_or_404(Whistleblower, pk=pk)
    whistleblower_log = None  # Initialize whistleblower_log
    latest_log = WhistleblowerLog.objects.filter(whistleblower=whistleblower).order_by('-created_at').first()

    if request.method == 'POST':
        profiling_choice = request.POST.get('profile')

        # Handle different profiling cases
        if profiling_choice == 'Statement query':
            form = StatementQueryForm(request.POST, instance=whistleblower)
            if form.is_valid():
                whistleblower.case_profiling_result = 'Statement query case initiated in CRM'
                form.save()
                whistleblower_log = WhistleblowerLog.objects.create(
                    key=whistleblower.key,
                    created_at=timezone.now(),
                    #comment=comment1,
                    status='Profiled',
                    user=request.user,  # Assign the current user directly
                    whistleblower=whistleblower  # Assign the whistleblower instance
                )
                #return redirect('wbview')
                messages.success(request, "Whistleblower case profiled as a statement querry.")
                return redirect(request.META.get('HTTP_REFERER', '/'))

        elif profiling_choice == 'Non Registered Employer':
            form = EmployerNotRegisteredForm(request.POST, instance=whistleblower)
            if form.is_valid():
                whistleblower.case_profiling_result = 'Non Registered Employer'
                form.save()
                whistleblower_log = WhistleblowerLog.objects.create(
                    key=whistleblower.key,
                    created_at=timezone.now(),
                    #comment=comment1,
                    status='Profiled',
                    user=request.user,  # Assign the current user directly
                    whistleblower=whistleblower  # Assign the whistleblower instance
                )                
                #return redirect('wbview')
                messages.success(request, "Whistleblower case profiled as Non Registered Employer.")
                return redirect(request.META.get('HTTP_REFERER', '/'))


        elif profiling_choice == 'Known member from a registered employer':
            form = EmployerRegisteredMemberKnownForm(request.POST, instance=whistleblower)
            if form.is_valid():
                # Handle logic based on conditions
                if form.cleaned_data['ongoing_audit']:
                    whistleblower.case_profiling_result = 'Assign to the current auditor'
                elif not form.cleaned_data['work_scope_known']:
                    whistleblower.case_profiling_result = 'Seek more info from the whistleblower'
                elif form.cleaned_data['work_scope_known'] and not form.cleaned_data['audited_recently_or_in_legal']:
                    whistleblower.case_profiling_result = 'Employer should be assigned for audit'
                elif not form.cleaned_data['ongoing_audit'] and form.cleaned_data['work_scope_known'] and form.cleaned_data['audited_recently_or_in_legal']:
                    whistleblower.case_profiling_result = 'Employer should be issued a demand note'
                form.save()
                whistleblower_log = WhistleblowerLog.objects.create(
                    key=whistleblower.key,
                    created_at=timezone.now(),
                    #comment=comment1,
                    status='Profiled',
                    user=request.user,  # Assign the current user directly
                    whistleblower=whistleblower  # Assign the whistleblower instance
                )                
                #return redirect('wbview')
                messages.success(request, "Whistleblower case profiled as Known member from a registered employer")
                return redirect(request.META.get('HTTP_REFERER', '/'))
            

        elif profiling_choice == 'UnKnown member from a registered employer':
            form = EmployerRegisteredMemberAnonymousForm(request.POST, instance=whistleblower)
            if form.is_valid():
                # Handle logic based on conditions similar to the above
                if form.cleaned_data['ongoing_audit']:
                    whistleblower.case_profiling_result = 'Assign to the current auditor'
                elif not form.cleaned_data['work_scope_known']:
                    whistleblower.case_profiling_result = 'Seek more info from the whistleblower'
                elif form.cleaned_data['work_scope_known'] and not form.cleaned_data['audited_recently_or_in_legal']:
                    whistleblower.case_profiling_result = 'Employer should be assigned for audit'
                elif form.cleaned_data['work_scope_known'] and form.cleaned_data['audited_recently_or_in_legal']:
                    whistleblower.case_profiling_result = 'Employer should be issued a demand note'
                form.save()
                whistleblower_log = WhistleblowerLog.objects.create(
                    key=whistleblower.key,
                    created_at=timezone.now(),
                    #comment=comment1,
                    status='Profiled',
                    user=request.user,  # Assign the current user directly
                    whistleblower=whistleblower  # Assign the whistleblower instance
                )                
                #return redirect('wbview')
                messages.success(request, "Whistleblower case profiled as UnKnown member from a registered employer")
                return redirect(request.META.get('HTTP_REFERER', '/'))
    
    else:
        form = BaseProfilingForm(instance=whistleblower)  # Initial form to select the profile

    return render(request, 'case_profiling22.html', {
        'form': form,
        'whistleblower': whistleblower,
        'whistleblower_log': whistleblower_log if whistleblower_log else whistleblower,
        'latest_status': latest_log.status if latest_log else whistleblower.status
    })

@login_required
def cases_with_comments_this_month(request):
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')  # Link to the Whistleblower model via the ForeignKey
    ).order_by('-created_at')  # Order logs by created_at (latest first)

    # Get the current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Filter comments that were added this month
    comments_this_month = Comment.objects.filter(
        date_added__year=current_year,
        date_added__month=current_month
    )

    # Get the associated whistleblower cases by matching the key in the comments
    whistleblower_keys = comments_this_month.values_list('key', flat=True).distinct()
    wbdata = Whistleblower.objects.filter(key__in=whistleblower_keys).annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),
            None
        ),
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest review_status
            None
        )
    ).order_by('-date_submitted')




    headline = 'Whistleblower cases that have received updates this month'



    # Check if the user belongs to the 'Auditors' group
    if request.user.groups.filter(name='Auditors').exists():
        # Filter the cases where bi_auditor_user_id matches the current user's ID
        wbdata = wbdata.filter(bi_auditor_user_id=str(request.user.id))
        headline = 'Whistleblower cases you have sent feedback this month'

    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'closewb',  # Example prefix for this view
        'button_action': 'Update',  # Example prefix for this view        
        
    }

        # Check the user group and render the appropriate template
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)

    else:
        # Handle the case when the user does not belong to any specific group
        return HttpResponse('Unauthorized', status=401)

    

@login_required

def closed_cases_view(request):
    # Subquery to get the latest log for each whistleblower
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')  # Link to the Whistleblower model via the ForeignKey
    ).order_by('-created_at')  # Order logs by created_at (latest first)

    # Annotating the whistleblower with the latest status from WhistleblowerLog, fallback to Whistleblower's status
    wbdata = Whistleblower.objects.annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),  # Use the latest status from WhistleblowerLog
            None#'status'  # Fallback to the Whistleblower's status
        ),        
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest update status
            None
        )

    ).filter(
        latest_status__in=['fully_settled','closed_try']  # Filter by the new state
    ).order_by('key', '-last_update')  # Order by key and last_update (distinct on the key)


    headline = 'Fully settled Whistleblower cases'

    # Check if the user belongs to the 'Auditors' group
    if request.user.groups.filter(name='Auditors').exists():
        # Filter the cases where bi_auditor_user_id matches the current user's ID
        wbdata = wbdata.filter(bi_auditor_user_id=str(request.user.id))
        headline = 'Fully settled Whistleblower case'

    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'editwb',  # Example prefix for this view
        'button_action': 'Feedback',  # Example prefix for this view
        
    }

    # Render the correct template based on the user's group
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)
    else:
        return HttpResponse('Unauthorized', status=401)






def cases_without_comments_this_month(request):
    # Get the current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Filter for comments added in the current month
    comments_this_month = Comment.objects.filter(
        date_added__year=current_year,
        date_added__month=current_month
    )

    # Get the whistleblower keys that have comments this month
    # Assuming 'key' in Comment refers to the Whistleblower's 'key'
    commented_keys = comments_this_month.values_list('key', flat=True).distinct()

    # Subquery to get the latest status from WhistleblowerLog
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')
    ).order_by('-created_at')

    # Filter whistleblower cases that either:
    # 1. Don't have any comments at all (i.e., cases that aren't in the Comment table)
    # 2. They have no comments for this month
    wbdata = Whistleblower.objects.filter(
        Q(key__isnull=True) | ~Q(key__in=commented_keys)  # Include cases with no comments or no comments this month
    ).annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),  # Use the latest status from WhistleblowerLog
            None
        ),
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest update status
            None
        )
    ).filter(
    Q(latest_status__isnull=True) | ~Q(latest_status__in=['fully_settled'])
    
    )

    headline = 'Whistleblower cases without feedback this month'

    # Check if the user belongs to the 'Auditors' group
    if request.user.groups.filter(name='Auditors').exists():
        # Filter the cases where bi_auditor_user_id matches the current user's ID
        wbdata = wbdata.filter(bi_auditor_user_id=str(request.user.id))
        headline = 'Whistleblower cases without feedback this month'

    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'editwb',  # Example prefix for this view
        'button_action': 'Feedback',  # Example prefix for this view
    }

    # Render the appropriate template based on user group
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)
    else:
        return HttpResponse('Unauthorized', status=401)
    

@login_required

def closed_cases_view(request):
    # Subquery to get the latest log for each whistleblower
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')  # Link to the Whistleblower model via the ForeignKey
    ).order_by('-created_at')  # Order logs by created_at (latest first)

    # Annotating the whistleblower with the latest status from WhistleblowerLog, fallback to Whistleblower's status
    wbdata = Whistleblower.objects.annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),  # Use the latest status from WhistleblowerLog
            None#'status'  # Fallback to the Whistleblower's status
        ),        
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest update status
            None
        )

    ).filter(
        latest_status__in=['fully_settled','closed_try']  # Filter by the new state
    ).order_by('key', '-last_update')  # Order by key and last_update (distinct on the key)


    headline = 'Fully settled Whistleblower cases'

    # Check if the user belongs to the 'Auditors' group
    if request.user.groups.filter(name='Auditors').exists():
        # Filter the cases where bi_auditor_user_id matches the current user's ID
        wbdata = wbdata.filter(bi_auditor_user_id=str(request.user.id))
        headline = 'Fully settled Whistleblower case'

    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'editwb',  # Example prefix for this view
        'button_action': 'Feedback',  # Example prefix for this view
        
    }

    # Render the correct template based on the user's group
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)
    else:
        return HttpResponse('Unauthorized', status=401)





@login_required
def cases_for_review(request):
    # Subquery to get the latest log for each whistleblower
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')  # Link to the Whistleblower model via the ForeignKey
    ).order_by('-created_at')  # Order logs by created_at (latest first)

    # Annotating the whistleblower with the latest status from WhistleblowerLog, fallback to Whistleblower's status
    wbdata = Whistleblower.objects.annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),  # Use the latest status from WhistleblowerLog
            None#'status'  # Fallback to the Whistleblower's status
        ),        
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest update status
            None
        )

    ).filter(
        latest_review_status__in=['Pending']  # Filter by the new state
    ).order_by('key', '-last_update')  # Order by key and last_update (distinct on the key)


    headline = 'Cases for review'

    # Check if the user belongs to the 'Auditors' group
    if request.user.groups.filter(name='Auditors').exists():
        # Filter the cases where bi_auditor_user_id matches the current user's ID
        wbdata = wbdata.filter(bi_auditor_user_id=str(request.user.id))
        headline = 'Fully settled Whistleblower case'

    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'editwb',  # Example prefix for this view
        'button_action': 'Feedback',  # Example prefix for this view
        
    }

    # Render the correct template based on the user's group
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)
    else:
        return HttpResponse('Unauthorized', status=401)
    

@login_required
def profilers_view(request):
    # Subquery to get the latest log for each whistleblower
    latest_log = WhistleblowerLog.objects.filter(
        whistleblower=OuterRef('pk')  # Link to the Whistleblower model via the ForeignKey
    ).order_by('-created_at')  # Order logs by created_at (latest first)

    # Annotating the whistleblower with the latest status from WhistleblowerLog, fallback to Whistleblower's status
    wbdata = Whistleblower.objects.annotate(
        latest_status=Coalesce(
            Subquery(latest_log.values('confirmed_status')[:1]),  # Use the latest status from WhistleblowerLog
            None#'status'  # Fallback to the Whistleblower's status
        ),        
        latest_review_status=Coalesce(
            Subquery(latest_log.values('review_status')[:1]),  # Get the latest review_status
            None
        ),
        latest_update_status=Coalesce(
            Subquery(latest_log.values('status')[:1]),  # Get the latest update status
            None
        )

    ).filter(
        case_profiling_result__isnull=True  # Only get cases where profile is null
    ).order_by('key', '-last_update')  # Order by key and last_update (distinct on the key)


    headline = 'Cases for profiling'


    context = {
        'wbdata': wbdata,
        'headline': headline,
        'url_prefix': 'editwb',  # Example prefix for this view
        'button_action': 'Feedback',  # Example prefix for this view
        
    }

    # Render the correct template based on the user's group
    if request.user.groups.filter(name='Auditors').exists():
        return render(request, 'view_wbcases_auditor.html', context)
    elif request.user.groups.filter(name='WB profiler').exists():
        return render(request, 'view_wbcases_profiler.html', context)
    elif request.user.groups.filter(name='WB reviewer').exists():
        return render(request, 'view_wbcases_reviewer.html', context)
    else:
        return HttpResponse('Unauthorized', status=401)