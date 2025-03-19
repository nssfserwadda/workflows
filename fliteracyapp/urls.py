from django.urls import path
from .import views

urlpatterns = [
    path('addEvent', views.addEvent, name="addEvent"),
    path('event_details/<int:event_id>/', views.event_details, name='event_details'),
    path('editEvent/<int:id>/', views.editEvent, name="editEvent"),
    path('deleteEvent/<int:id>/', views.deleteEvent, name="deleteEvent"),
    path('memsearch', views.membersearch, name="memsearch"),


   

]