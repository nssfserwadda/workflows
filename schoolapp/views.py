
# Create your views here.
# school/views.py
from django.shortcuts import render
from django.http import JsonResponse
import json
from django.shortcuts import render, redirect
from .forms import StudentRegistrationForm

from .models import SpreadsheetData
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('register_student')  # Redirect to a success URL after successful registration
    else:
        form = StudentRegistrationForm()
    return render(request, 'register_student.html', {'form': form})



def spreadsheet_input(request):
    return render(request, 'spreadsheet_input.html')



# @csrf_exempt  # For simplicity (better use csrf tokens in production)
# def save_spreadsheet_data(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)

#         for row in data:
#             SpreadsheetData.objects.create(
#                 name=row.get('name', ''),
#                 email=row.get('email', ''),
#                 phone=row.get('phone', ''),
#                 salary=float(row.get('salary', 0))
#             )
#         return JsonResponse({'status': 'success'})
    
#     return JsonResponse({'status': 'failed'}, status=400)


# from django.views.decorators.csrf import csrf_exempt
# import json
# from django.http import JsonResponse
# from .models import SpreadsheetData

@csrf_exempt
def save_spreadsheet_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        errors = []

        for idx, row in enumerate(data, start=1):
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()
            phone = row.get('phone', '').strip()
            salary = row.get('salary', 0)

            # Server-side validations
            if not name or not name.replace(' ', '').isalpha():
                errors.append(f"Row {idx}: Invalid name '{name}'.")
                continue

            try:
                validate_email(email)
            except ValidationError:
                errors.append(f"Row {idx}: Invalid email '{email}'.")
                continue

            if not phone or len(phone) < 7:
                errors.append(f"Row {idx}: Invalid phone number '{phone}'.")
                continue

            try:
                salary = float(salary)
                if salary < 0:
                    raise ValueError()
            except ValueError:
                errors.append(f"Row {idx}: Invalid salary '{salary}'.")
                continue

            # Save valid data
            SpreadsheetData.objects.create(
                name=name,
                email=email,
                phone=phone,
                salary=salary
            )

        if errors:
            return JsonResponse({'status': 'partial', 'errors': errors}, status=400)

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'failed'}, status=400)

