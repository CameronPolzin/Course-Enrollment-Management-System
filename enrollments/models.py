from django.db import models
from django.conf import settings

from courses.models import Course


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.course_code}"
    
class EnrollmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]

    # Student submitting the request
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollment_requests'
    )

    # Course being requested
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollment_requests'
    )
    
    # Student explanation for special enrollment
    reason = models.TextField(blank=True)
    
    # Request status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Timestamp for request creation
    created_at = models.DateTimeField(auto_now_add=True)

    # The reason/issue for the special request
    ISSUE_CHOICES = [
        ('full', 'Course Full'),
        ('prerequisites', 'Missing Prerequisites'),
    ]
    issue = models.CharField(
        max_length=20,
        choices=ISSUE_CHOICES,
        default='full'
    )

    class Meta:
        # Prevent duplicate requests for same student/course
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} request for {self.course.course_code} ({self.status})"
    
class Waitlist(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='waitlists'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='waitlists'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} waitlisted for {self.course.course_code}"   