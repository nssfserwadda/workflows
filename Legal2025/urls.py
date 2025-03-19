from django.urls import path
from .import views

urlpatterns = [
path("legalfiles/", views.view_legalfiles, name="legalfiles"),
path('addfile/', views.legal_file_record, name='addfile'),
path('update_legalfile/<int:id>/', views.update_legal_file_advocate, name='update_legalfile'),
path('update_legalfilemanager/<int:id>/', views.add_manager_comment, name='update_legalfile_manager'),
path('delete_legalfile/<int:id>/', views.legal_file_record, name='delete_legalfile'),
path('assign-file/', views.assign_file, name='assign_file'),
path('files_toassign/', views.Legal_Files_to_assign, name='files_toassign'),
path('assigned_files/', views.Assigned_legal_files, name='assigned_files'),
path('details_offiles/<int:id>/', views.detail_legalfile, name='details_offiles'),

#Search files 
path("search_files/", views.search_legalfiles, name="search_files"),
path('search_files/details_offiles/<int:id>/', views.detail_legalfile, name='details_offiles'),


#Agreements and installments
path('agreements/', views.agreement_list, name='agreement_list'),
path('agreements/<int:agreement_id>/installments/add/', views.add_installment, name='add_installment'),
path('installments/<int:installment_id>/update/', views.edit_installment, name='update_installment'),
path('installments/<int:installment_id>/', views.installment_detail, name='installment_detail'),

#path('installments/', views.installment_list, name='installment_list'),
path('agreements/<int:agreement_id>/installments/', views.installment_list, name='installment_list'),
path('legalfiles/<int:legal_file_id>/agreements/add/', views.add_agreement, name='add_agreement'),
#path("check_trn_status/", views.check_trn_status, name="check_trn_status"),
# path("check_trn_payment/", views.check_trn_payment_status, name="check_trn_payment"),
# # path("check_trn_payment/<str:trn>/<int:legal_file_id>/", views.check_trn_payment_status, name="check_trn_payment"),
path("check_trn_payment/<str:trn>/<int:legal_file_id>/", views.check_trn_payment_status, name="check_trn_payment"),


path("calendar/", views.calendar_view, name="hearing_calendar"),


]