

# Create your views here.
from django.shortcuts import render, redirect

from django.http import HttpResponse
from .forms import FeedbackForm
from .models import JotFeedback #Generalquery # new

def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('submit_feedback')  # Redirect to a thank-you page or any other desired page
    else:
        form = FeedbackForm()

    return render(request, 'dist\index.html', {'form': form})


def your_view(request):
    return render(request, '\doc1.html')


# def jotfeedback(request):
#     return render(request, 'jotfeedback.html')

def submit_jotfeedback(request):
    if request.method == "POST":
        # Handle form submission
        return redirect('success_page')  # Change to your actual success URL
    return render(request, 'jotfeedback.html')


def submit_jotfeedback(request):
    if request.method == 'POST':
        # Retrieve data directly from the request
        fcr_resolved = request.POST.get('fcr_resolved')
        ces_easy = request.POST.get('ces_easy')
        overall_satisfaction = request.POST.get('overall_satisfaction')
        additional_comments = request.POST.get('additional_comments')
        nps_rating = request.POST.get('nps_rating')
        first_name = request.POST.get('first_name')
        yourphone = request.POST.get('yourphone')
        csobranch = request.POST.get('csobranch')
        csoname = request.POST.get('csoname')
        tstamp = request.POST.get('tstamp')

        # Create a JotFeedback instance and save it to the database
        jot_feedback = JotFeedback.objects.create(
            nps_rating=nps_rating,
            fcr_resolved=fcr_resolved,
            ces_easy=ces_easy,
            overall_satisfaction=overall_satisfaction,
            additional_comments=additional_comments,
            first_name=first_name,
            yourphone=yourphone,
            csobranch=csobranch,
            csoname=csoname,
            tstamp=tstamp
        )

        # Optionally, you can do additional processing or redirect to a success page
        return HttpResponse('Thank you for submitting your feedback')

    else:
        # Handle non-POST requests if necessary
        return HttpResponse('Invalid request method')