from django.urls import path
from .import views
#from suspenseapp.views import suspensesearch


urlpatterns = [

    path('startpg/', views.start_page_view, name='startpg'),
    path('susp_quer/', views.other_suspense_summary_view, name='susp_quer'),

    path('msp_search/', views.suspensesearch, name='msp_search'),
    path('esp_search/', views.empl_suspensesearch, name='esp_search'),
    path('nsf_search/', views.nsf_suspensesearch, name='nsf_search'),
    path('sum_search/', views.search_suspense_summary, name='sum_search'),
    path('susp_all/', views.search_all_suspense, name='susp_all'),
    path('susp_suma/', views.search_suspense_summary, name='susp_suma'),
    path('uratins/', views.search_ura_tins, name='uratins'),

    path('susp_comp/', views.compare_suspense_view, name='susp_comp'),
    path('susp_comp2/', views.compare_suspense_view222, name='susp_comp2'),
    path('download/', views.download_results, name='download_results'),
    path('emp_hist/', views.search_employmeny_history, name='emp_hist'),

    path('leads/', views.suspense_leads_view, name='leads'),
    
    
]
