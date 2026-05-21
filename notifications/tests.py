from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from courses.models import Course
from enrollments.models import Enrollment
from .models import Notification

User = get_user_model()

class NotificationIntegrationTests(TestCase):
    """
    Integration tests to verify the interaction between User, Course, Enrollment, and Notification models.
    """
    def setUp(self):
        # Create an instructor
        self.instructor = User.objects.create_user(
            username='inst_int',
            password='password123',
            role='instructor'
        )
        # Create a course
        self.course = Course.objects.create(
            name='Integration Course',
            course_code='INT101',
            instructor=self.instructor
        )
        # Create a student and enroll them
        self.student = User.objects.create_user(
            username='stud_int',
            password='password123',
            role='student'
        )
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_notification_creation_on_message_send(self):
        """
        Verify that sending a message through the view correctly creates Notification objects.
        """
        self.client.login(username='inst_int', password='password123')
        self.client.post(reverse('send_notification'), {
            'course_id': self.course.id,
            'message': 'Integration Test Message'
        })
        
        # Verify notification exists in database for the student
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 1)
        notif = Notification.objects.get(user=self.student)
        self.assertEqual(notif.message, "[INT101] Integration Test Message")

    def test_unread_count_integration(self):
        """
        Verify that the unread_notifications_count property on the User model works correctly.
        """
        self.assertEqual(self.student.unread_notifications_count, 0)
        Notification.objects.create(user=self.student, message="Test")
        self.assertEqual(self.student.unread_notifications_count, 1)


class NotificationAcceptanceTests(TestCase):
    """
    Acceptance tests based on the User Story:
    As an instructor, I want to message students so that I can communicate updates.
    """
    def setUp(self):
        self.client = Client()
        # Data setup
        self.instructor = User.objects.create_user(username='instructor_acc', password='password123', role='instructor')
        self.student = User.objects.create_user(username='student_acc', password='password123', role='student')
        self.course = Course.objects.create(name='Acceptance Course', course_code='ACC101', instructor=self.instructor)
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_instructor_sends_notification_successfully(self):
        """
        Given an instructor is on the notifications page
        And a class is selected from a dropdown
        When a message is sent
        Then all enrolled students receive the message
        """
        # Given an instructor is on the send notifications page
        self.client.login(username='instructor_acc', password='password123')
        response = self.client.get(reverse('send_notification'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send Notification to Class")
        self.assertContains(response, "ACC101")

        # When a message is sent
        response = self.client.post(reverse('send_notification'), {
            'course_id': self.course.id,
            'message': 'Important Update'
        })
        self.assertRedirects(response, reverse('notifications'))

        # Then all enrolled students receive the message
        self.client.login(username='student_acc', password='password123')
        response = self.client.get(reverse('notifications'))
        self.assertContains(response, "[ACC101] Important Update")
        self.assertEqual(self.student.unread_notifications_count, 1)

    def test_mark_all_read_acceptance(self):
        """
        Verify that a student can mark their notifications as read.
        """
        Notification.objects.create(user=self.student, message="Alert")
        self.client.login(username='student_acc', password='password123')
        
        # Verify it shows as unread (notif-unread class in template)
        response = self.client.get(reverse('notifications'))
        self.assertContains(response, "notif-unread")

        # Mark all as read
        self.client.post(reverse('notifications'), {'mark_read': '1'})
        
        # Verify it no longer shows as unread
        response = self.client.get(reverse('notifications'))
        self.assertNotContains(response, "notif-unread")
        self.assertEqual(self.student.unread_notifications_count, 0)

    def test_admin_sends_notification_successfully(self):
        """
        Verify that an admin can send a message to any class.
        """
        admin = User.objects.create_user(username='admin_acc', password='password123', role='admin')
        
        self.client.login(username='admin_acc', password='password123')
        
        # Admin should see all courses
        response = self.client.get(reverse('send_notification'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ACC101")
        
        # Admin sends a message
        response = self.client.post(reverse('send_notification'), {
            'course_id': self.course.id,
            'message': 'Admin Update'
        })
        self.assertRedirects(response, reverse('notifications'))
        
        # Student receives it
        self.client.login(username='student_acc', password='password123')
        response = self.client.get(reverse('notifications'))
        self.assertContains(response, "[ACC101] Admin Update")
