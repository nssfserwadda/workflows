from django.urls import path
from .import views


urlpatterns = [

    path('register_student/', views.register_student, name='register_student'),
    path('spreadsheet/', views.spreadsheet_input, name='spreadsheet_input'),
    path('save-spreadsheet/', views.save_spreadsheet_data, name='save_spreadsheet_data'),
]

