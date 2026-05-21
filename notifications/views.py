from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Course
from enrollments.models import Enrollment
from .models import Notification

@login_required
def notifications_view(request):
    """
    Displays the user's notifications.
    Also handles POST requests to mark all notifications as read.
    """
    if request.method == 'POST':
        if 'mark_read' in request.POST:
            # Mark all unread notifications as read
            request.user.notifications.filter(is_read=False).update(is_read=True)
            return redirect('notifications')

    notifications = request.user.notifications.all()
    context = {'notifications': notifications}
        
    return render(request, 'notifications/notifications.html', context)

@login_required
def send_notification_view(request):
    """
    Allows instructors to send messages to their classes,
    and admins to send messages to any class.
    """
    if request.user.role not in ['instructor', 'admin']:
        return redirect('notifications')

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        message_text = request.POST.get('message')
        if course_id and message_text:
            try:
                if request.user.role == 'admin':
                    course = Course.objects.get(id=course_id)
                else:
                    course = Course.objects.get(id=course_id, instructor=request.user)
                
                enrollments = Enrollment.objects.filter(course=course)
                for enrollment in enrollments:
                    Notification.objects.create(
                        user=enrollment.student,
                        message=f"[{course.course_code}] {message_text}"
                    )
            except Course.DoesNotExist:
                pass # Or handle error
        return redirect('notifications')

    context = {}
    if request.user.role == 'instructor':
        context['courses'] = request.user.courses_taught.all()
    elif request.user.role == 'admin':
        context['courses'] = Course.objects.all()
        
    return render(request, 'notifications/send_notification.html', context)
