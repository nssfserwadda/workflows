from django.conf import settings
#from django.shortcuts import render

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404
from .forms import Fl_eventForm, RegisterAttendantForm, SearchMemberForm  # new
from .models import Fl_event, Attachment, Nssfmember, Fl_attendants  # new
from django.contrib import messages  # new
from django.http import HttpResponseRedirect
from .forms import RegisterAttendantForm


@login_required
def addEvent(request):
    if request.method == "POST":
        fm = Fl_eventForm(request.POST, request.FILES)

        #event = get_object_or_404(Fl_event, id=id)
        #attachments = Attachment.objects.filter(event=event)

        if fm.is_valid():
            fl_event = fm.save(commit=False)
            fl_event.save()
            # If you need to handle attachments separately, do it here
            attachments = request.FILES.getlist('attachments')
            # And then save each attachment with the corresponding event

            for attachment in attachments:
                Attachment.objects.create(fl_event=fl_event, file=attachment)
            
            messages.success(request, 'FL Event Added Successfully')
            return redirect('addEvent')  # Redirect after successful form submission
        else:
            #messages.success(request, 'Check the data captured')
            messages.add_message(request, messages.ERROR, 'Failed record capture, crosscheck the field entries')
            return redirect('addEvent')        

    else:
        fm = Fl_eventForm()
    
    eventdata = Fl_event.objects.all().order_by('-id')
    return render(request, 'eventspage5.html', {'fm': fm, 'eventdata': eventdata})
    #return render(request, 'eventspage5.html', {'fm': fm, 'eventdata': eventdata, 'attachments': attachments})

@login_required
def deleteEvent(request, id):
    Fl_event.objects.get(pk=id).delete()
    messages.success(request, 'Event Record Deleted')
    return redirect('addEvent')

      
@login_required
def editEvent(request, id):
    instance = Fl_event.objects.get(pk=id)
    if request.method == "POST":
        fm = Fl_eventForm(request.POST, request.FILES, instance=instance)
        if fm.is_valid():
            fl_event = fm.save(commit=False)
            fl_event.save()
            # If you need to handle attachments separately, do it here
            attachments = request.FILES.getlist('attachments')
            # And then save each attachment with the corresponding event

            for attachment in attachments:
                Attachment.objects.create(fl_event=fl_event, file=attachment)
                
            messages.success(request, 'Event Record Updated')
            return redirect('addEvent')
    else:
        initial_data = {}
        for field in Fl_event._meta.fields:
            if getattr(instance, field.name) is None:
                initial_data[field.name] = ''  # Set empty string for fields with None values
        fm = Fl_eventForm(instance=instance, initial=initial_data)
        advisors = ['Anna Maria Sanyu', 'Aisha Nakanwagi', 'Jackline Nagasha', 'Appolo Mbowa Kibirango']
        return render(request, 'edit_event22.html', context={'fm': fm, 'advisors': advisors})


@login_required
def event_details(request, event_id):
    event = get_object_or_404(Fl_event, pk=event_id)
    #event = get_object_or_404(Fl_event, id=id)
    attachments = Attachment.objects.filter(fl_event=event)
    
    # Retrieve attendees for the event
    #attendees = Fl_attendants.objects.filter(event_name=event.event_name, event_date=event.event_date)
    attendees = Fl_attendants.objects.filter(event_name=event.event_name, event_date=event.event_date).order_by('-id')

    # Initialize form for searching members
    search_form = SearchMemberForm(request.GET or None)
    results = []
    if request.method == "GET":
        if search_form.is_valid():
            query = search_form.cleaned_data['q']
            results = Nssfmember.objects.filter(name__icontains=query)

    # Handle registration of member for event using search
    if 'register_member_id' in request.GET:
        member_id = request.GET.get('register_member_id')
        member = get_object_or_404(Nssfmember, pk=member_id)
        Fl_attendants.objects.create(
            name=member.name,
            nssf_number=member.nssf_number,
            event_name=event.event_name,
            event_date=event.event_date
        )
        return redirect('event_details', event_id=event_id)

    # Handle registration of member for event without searching
    if request.method == 'POST':
        register_form = RegisterAttendantForm(request.POST)
        if register_form.is_valid():
            name = register_form.cleaned_data['name']
            #nssf_number = register_form.cleaned_data['nssf_number']
            Fl_attendants.objects.create(
                name=name,
                #nssf_number=nssf_number,
                event_name=event.event_name,
                event_date=event.event_date
            )
            return redirect('event_details', event_id=event_id)
    else:
        register_form = RegisterAttendantForm()

    # Handle deletion of attendant
    if 'delete_attendant_id' in request.POST:
        attendant_id = request.POST.get('delete_attendant_id')
        attendant = get_object_or_404(Fl_attendants, pk=attendant_id)
        attendant.delete()
        return HttpResponseRedirect(request.path)  # Redirect to the same page after deletion

    return render(request, 'event_details3.html', {'event': event, 'attendees': attendees, 'search_form': search_form, 'results': results, 'register_form': register_form, 'attachments': attachments})


def membersearch(request):

    # Initialize form for searching members
    search_form = SearchMemberForm(request.GET or None)
    results = []
    if request.method == "GET":
        if search_form.is_valid():
            query = search_form.cleaned_data['q']
            results = Nssfmember.objects.filter(name__icontains=query)

    return render(request, 'membersearch.html', {'search_form': search_form, 'results': results})
