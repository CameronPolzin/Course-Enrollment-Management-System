from django.urls import path
from . import views

urlpatterns = [
    path('<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
]