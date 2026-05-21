from django.urls import path
from .views import admin_dashboard, instructor_dashboard, register, student_dashboard, user_login, home, user_logout, edit_users, update_user, delete_user


urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('admin_dashboard/', admin_dashboard),
    path('instructor_dashboard/', instructor_dashboard),
    path('student_dashboard/', student_dashboard),
    path('logout/', user_logout, name='logout'),
    path('edit_users/', edit_users, name='edit_users'),

    path('edit_users/update/<int:user_id>/', update_user, name='update_user'),
    path('edit_users/delete/<int:user_id>/', delete_user, name='delete_user'),
]
