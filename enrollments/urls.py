from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('drop-course/<int:course_id>/', views.drop_course, name='drop_course'),
    path('my-enrollments/', views.my_enrollments, name='my_enrollments'),
    path('enrollment-history/', views.enrollment_history, name='enrollment_history'),
    path('request/<int:course_id>/',views.submit_enrollment_request,name='submit_enrollment_request'),
    path('manage/<int:course_id>/', views.manage_enrollment, name='manage_enrollment'),
    path('waitlist/<int:course_id>/', views.join_waitlist, name='join_waitlist'),
    path('my_schedule/', views.my_schedule, name='my_schedule'),
    path('reports/',views.enrollment_reports,name='enrollment_reports'),
    path('waitlist-status/', views.waitlist_status, name='waitlist_status'),
]