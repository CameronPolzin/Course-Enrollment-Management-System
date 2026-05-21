from django.urls import path
from .views import notifications_view, send_notification_view

urlpatterns = [
    path('', notifications_view, name='notifications'),
    path('send/', send_notification_view, name='send_notification'),
]
