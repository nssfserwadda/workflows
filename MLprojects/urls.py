from django.urls import path
from .import views


urlpatterns = [
    path('sectorz', views.upload_file, name="sectorz"),
    path('download/', views.download_results, name='download_results'),

]