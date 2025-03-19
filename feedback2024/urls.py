from django.urls import path
from .import views


urlpatterns = [
    
    path('sucs/', views.success_view, name='sucs'),
    #path('editwb/<int:pk>/', views.edit_whistleblower, name='edit_whistleblower'),
    path("wbview/", views.view_wbcases, name="wbview"),
    path("wbview/editwb/<int:pk>/", views.edit_whistleblower, name="editwb"),
    path("wbview/closewb/<int:pk>/", views.close_by_auditor, name="closewb"),
    path("wbview/review_closure/<int:pk>/", views.review_closure, name="review_closure"),
    path("wbview/profile/<int:pk>/", views.case_profiling, name="profile"),
    
    path("fedbk/", views.cases_with_comments_this_month, name="fedbk"),
    path("fedbk/editwb/<int:pk>/", views.edit_whistleblower, name="editwb"),
    path("fedbk/closewb/<int:pk>/", views.close_by_auditor, name="closewb"),
    path("fedbk/review_closure/<int:pk>/", views.review_closure, name="review_closure"),
    path("fedbk/profile/<int:pk>/", views.case_profiling, name="profile"),

    path("clsd/", views.closed_cases_view, name="clsd"),
    path("clsd/editwb/<int:pk>/", views.edit_whistleblower, name="editwb"),
    path("clsd/closewb/<int:pk>/", views.close_by_auditor, name="closewb"),
    path("clsd/review_closure/<int:pk>/", views.review_closure, name="review_closure"),
    path("clsd/profile/<int:pk>/", views.case_profiling, name="profile"),

    path("nofedbk/", views.cases_without_comments_this_month, name="nofedbk"),
    path("nofedbk/editwb/<int:pk>/", views.edit_whistleblower, name="editwb"),
    path("nofedbk/closewb/<int:pk>/", views.close_by_auditor, name="closewb"),
    path("nofedbk/review_closure/<int:pk>/", views.review_closure, name="review_closure"),
    path("nofedbk/profile/<int:pk>/", views.case_profiling, name="profile"),

    path("case_rev/", views.cases_for_review, name="case_rev"),
    path("case_rev/review_closure/<int:pk>/", views.review_closure, name="review_closure"),

    path("prof_vew/", views.profilers_view, name="prof_vew"),
    path("prof_vew/profile/<int:pk>/", views.case_profiling, name="profile"),
    
    
    #path("engagview/emp_eng/<int:id>/", views.employer_engagements, name="emp_eng"),
    
        
]
