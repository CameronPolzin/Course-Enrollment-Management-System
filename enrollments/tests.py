from urllib import request, response
from django.test import TestCase, Client
from django.urls import reverse
from courses.models import Course
from enrollments.models import Enrollment, EnrollmentRequest, Waitlist
from notifications.models import Notification
from users.models import User


class EnrollmentTests(TestCase):

    def setUp(self):
        self.client = Client()


        #test for admin
        self.admin = User.objects.create_user(
            username='admin1',
            password='testpass123',
            role='admin'
        )
        
        #test for different users and role
        self.student = User.objects.create_user(
            username='student1',
            password='testpass123',
            role='student'
        )

        self.other_student = User.objects.create_user(
            username='student2',
            password='testpass123',
            role='student'
        )

        self.instructor = User.objects.create_user(
            username='instructor1',
            password='testpass123',
            role='instructor'
        )

        self.course = Course.objects.create(
            name='Software Engineering',
            course_code='CS361',
            description='Intro to Software Engineering',
            seating_limit=2,
            instructor=self.instructor
        )

    def test_student_can_enroll_when_seats_available(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('enrollments:enroll_course', args=[self.course.id]))
        self.assertEqual(Enrollment.objects.count(), 1, 'Enrollment record should be created.')

    def test_enrollment_rejected_when_course_is_full(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.other_student, course=self.course)

        third_student = User.objects.create_user(
            username='student3',
            password='testpass123',
            role='student'
        )

        self.client.login(username='student3', password='testpass123')
        response = self.client.post(reverse('enrollments:enroll_course', args=[self.course.id]))
        self.assertEqual(Enrollment.objects.count(), 2, 'Enrollment should be rejected when course is full.')

    def test_duplicate_enrollment_is_prevented(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('enrollments:enroll_course', args=[self.course.id]))
        self.assertEqual(Enrollment.objects.count(), 1, 'Duplicate enrollment should be prevented.')

    def test_non_student_cannot_enroll(self):
        self.client.login(username='instructor1', password='testpass123')
        response = self.client.post(reverse('enrollments:enroll_course', args=[self.course.id]))
        self.assertEqual(Enrollment.objects.count(), 0, 'Only students should be allowed to enroll.')

    def test_admin_can_view_enrollment_history(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('enrollments:enrollment_history'))
        self.assertEqual(response.status_code, 200, 'Admin should be able to view enrollment history.')

    def test_enrollment_history_displays_records(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('enrollments:enrollment_history'))
        self.assertContains(response, 'student1')


    def test_non_admin_cannot_view_enrollment_history(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('enrollments:enrollment_history'))
        self.assertEqual(response.status_code, 302, 'Non-admin should be redirected away from enrollment history.')

    def test_admin_can_access_manage_enrollment_page(self):
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(
            reverse('enrollments:manage_enrollment', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200, 'Admin should be able to access manage enrollment page.')


    def test_instructor_can_access_own_course_manage_enrollment_page(self):
        self.client.login(username='instructor1', password='testpass123')
        response = self.client.get(
            reverse('enrollments:manage_enrollment', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200, 'Assigned instructor should be able to manage enrollment.')
    
    def test_student_cannot_access_manage_enrollment_page(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('enrollments:manage_enrollment', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 302, 'Student should be redirected away from manage enrollment page.')


    def test_unassigned_instructor_cannot_manage_course_enrollment(self):
        self.client.login(username='instructor2', password='testpass123')
        response = self.client.get(
            reverse('enrollments:manage_enrollment', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 302, 'Instructor should not manage courses they are not assigned to.')


    def test_admin_can_add_student_to_course(self):
        self.client.login(username='admin1', password='testpass123')
        self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course.id]),
            {
                'action': 'add',
                'student_id': self.student.id
            }
        )
        self.assertEqual(Enrollment.objects.count(), 1, 'Admin should be able to add a student to a course.')


    def test_instructor_can_add_student_to_own_course(self):
        self.client.login(username='instructor1', password='testpass123')
        self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course.id]),
            {
                'action': 'add',
                'student_id': self.student.id
            }
        )
        self.assertEqual(Enrollment.objects.count(), 1, 'Instructor should be able to add a student to their own course.')


    def test_admin_can_remove_student_from_course(self):
        Enrollment.objects.create(student=self.student, course=self.course)

        self.client.login(username='admin1', password='testpass123')
        self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course.id]),
            {
                'action': 'remove',
                'student_id': self.student.id
            }
        )
        self.assertEqual(Enrollment.objects.count(), 0, 'Admin should be able to remove a student from a course.')


    def test_instructor_can_remove_student_from_own_course(self):
        Enrollment.objects.create(student=self.student, course=self.course)

        self.client.login(username='instructor1', password='testpass123')
        self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course.id]),
            {
                'action': 'remove',
                'student_id': self.student.id
            }
        )
        self.assertEqual(Enrollment.objects.count(), 0, 'Instructor should be able to remove a student from their own course.')

    #test for waitlist
    def test_student_can_join_waitlist_when_course_is_full(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.other_student, course=self.course)

        third_student = User.objects.create_user(
            username='student3',
            password='testpass123',
            role='student'
        )
        self.client.login(username='student3', password='testpass123')
        self.client.post(reverse('enrollments:join_waitlist', args=[self.course.id]))
        self.assertEqual(Waitlist.objects.count(), 1, 'Student should be added to waitlist when course is full.')


    def test_student_cannot_join_waitlist_twice(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.other_student, course=self.course)
        third_student = User.objects.create_user(
            username='student3',
            password='testpass123',
            role='student'
        )

        Waitlist.objects.create(student=third_student, course=self.course)
        self.client.login(username='student3', password='testpass123')
        self.client.post(reverse('enrollments:join_waitlist', args=[self.course.id]))
        self.assertEqual(Waitlist.objects.count(), 1, 'Duplicate waitlist entry should be prevented.')


    def test_student_cannot_join_waitlist_when_course_has_seats(self):
        self.client.login(username='student1', password='testpass123')
        self.client.post(reverse('enrollments:join_waitlist', args=[self.course.id]))
        self.assertEqual(Waitlist.objects.count(), 0, 'Student should not join waitlist if course is not full.')


    def test_non_student_cannot_join_waitlist(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.other_student, course=self.course)
        self.client.login(username='instructor1', password='testpass123')
        self.client.post(reverse('enrollments:join_waitlist', args=[self.course.id]))
        self.assertEqual(Waitlist.objects.count(), 0, 'Only students should be able to join waitlist.')

    def test_waitlisted_student_is_promoted_when_seat_opens(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.other_student, course=self.course)   
        waitlist_student = User.objects.create_user(
            username='student3',
            password='testpass123',
            role='student'
        )

        Waitlist.objects.create(student=waitlist_student, course=self.course)
        self.client.login(username='admin1', password='testpass123')
        self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course.id]),
            {
                'action': 'remove',
                'student_id': self.student.id
            }
        )
        self.assertTrue(
            Enrollment.objects.filter(student=waitlist_student, course=self.course).exists(),
            'Waitlisted student should be promoted when a seat opens.'
        )
        self.assertFalse(
            Waitlist.objects.filter(student=waitlist_student, course=self.course).exists(),
            'Waitlist record should be removed after promotion.'
        )

    #Waitlist status
    def test_student_can_view_waitlist_status_page(self):
        Waitlist.objects.create(student=self.student, course=self.course)
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('enrollments:waitlist_status'))
        self.assertEqual(response.status_code, 200, 'Student should be able to view waitlist status page.')


    def test_waitlist_status_displays_course(self):
        Waitlist.objects.create(student=self.student, course=self.course)
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('enrollments:waitlist_status'))
        self.assertContains(response, 'CS361')


    def test_waitlist_status_displays_position(self):
        Waitlist.objects.create(student=self.other_student, course=self.course)
        Waitlist.objects.create(student=self.student, course=self.course)
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('enrollments:waitlist_status'))
        self.assertContains(response, '2')


    def test_non_student_cannot_view_waitlist_status(self):
        self.client.login(username='instructor1', password='testpass123')
        response = self.client.get(reverse('enrollments:waitlist_status'))
        self.assertEqual(response.status_code, 302, 'Non-students should be redirected away from waitlist status page.')




class DropCourseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student1',
            password='testpass123',
            role='student'
        )

        self.other_student = User.objects.create_user(
            username='student2',
            password='testpass123',
            role='student'
        )

        self.instructor = User.objects.create_user(
            username='instructor1',
            password='testpass123',
            role='instructor'
        )

        self.course = Course.objects.create(
            name='Software Engineering',
            course_code='CS361',
            description='Intro to Software Engineering',
            seating_limit=2,
            instructor=self.instructor
        )

    def test_student_can_drop_course(self):
        Enrollment.objects.create(student=self.student, course=self.course)

        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('enrollments:drop_course', args=[self.course.id]))
        self.assertEqual(Enrollment.objects.count(), 0, 'Enrollment should be removed after dropping.')

    def test_non_student_cannot_drop(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='instructor1', password='testpass123')
        response = self.client.post(reverse('enrollments:drop_course', args=[self.course.id]))
        self.assertEqual(Enrollment.objects.count(), 1, 'Non-students should not be able to drop courses.')

    def test_dropped_course_not_in_enrollments_view(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='student1', password='testpass123')
        self.client.post(reverse('enrollments:drop_course', args=[self.course.id]))
        response = self.client.get(reverse('enrollments:my_enrollments'))
        self.assertNotContains(response, 'Software Engineering')
        
class EnrollmentRequestTests(TestCase):

    def setUp(self):
        # Create student user
        self.student = User.objects.create_user(
            username='student1',
            password='password123',
            role='student'
        )

        # Create instructor user
        self.instructor = User.objects.create_user(
            username='instructor1',
            password='password123',
            role='instructor'
        )

        # Create test course
        self.course = Course.objects.create(
            name='Algorithms',
            course_code='CS361',
            seating_limit=1
        )

    def test_student_can_submit_request(self):
        """
        Verify a student can successfully submit
        an enrollment request.
        """
        # Log in as student
        self.client.login(
            username='student1',
            password='password123'
        )

        # Submit request with reason
        response = self.client.post(
            f'/enrollments/request/{self.course.id}/',
            {
                'reason': 'Need this course to graduate.'
            }
        )

        # Verify redirect after success
        self.assertEqual(response.status_code, 302)

        # Verify request exists in database
        self.assertTrue(
            EnrollmentRequest.objects.filter(
                student=self.student,
                course=self.course
            ).exists()
        )

    def test_request_status_defaults_to_pending(self):
        """
        Verify request status defaults to pending.
        """
        enrollment_request = EnrollmentRequest.objects.create(
            student=self.student,
            course=self.course,
            reason='Need special enrollment.'
        )

        # Verify default status
        self.assertEqual(
            enrollment_request.status,
            'pending'
        )

    def test_duplicate_requests_are_prevented(self):
        """
        Verify duplicate requests cannot be created.
        """
        # Create initial request
        EnrollmentRequest.objects.create(
            student=self.student,
            course=self.course,
            reason='First request.'
        )

        # Log in student
        self.client.login(
            username='student1',
            password='password123'
        )

        # Attempt duplicate request
        self.client.post(
            f'/enrollments/request/{self.course.id}/',
            {
                'reason': 'Duplicate request.'
            }
        )

        # Verify only one request exists
        self.assertEqual(
            EnrollmentRequest.objects.filter(
                student=self.student,
                course=self.course
            ).count(),
            1
        )

    def test_non_students_cannot_submit_requests(self):
        """
        Verify instructors/admins cannot submit requests.
        """
        # Log in as instructor
        self.client.login(
            username='instructor1',
            password='password123'
        )

        # Attempt request submission
        self.client.post(
            f'/enrollments/request/{self.course.id}/',
            {
                'reason': 'Instructor should not request.'
            }
        )

        # Verify request was NOT created
        self.assertFalse(
            EnrollmentRequest.objects.filter(
                course=self.course
            ).exists()
        )

    def test_request_links_student_and_course(self):
        """
        Verify request links correct student and course.
        """
        enrollment_request = EnrollmentRequest.objects.create(
            student=self.student,
            course=self.course,
            reason='Need enrollment.'
        )

        # Verify correct associations
        self.assertEqual(
            enrollment_request.student,
            self.student
        )

        self.assertEqual(
            enrollment_request.course,
            self.course
        )

    def test_reason_is_saved(self):
        """
        Verify submitted reason is saved correctly.
        """
        enrollment_request = EnrollmentRequest.objects.create(
            student=self.student,
            course=self.course,
            reason='Graduation requirement.'
        )

        self.assertEqual(
            enrollment_request.reason,
            'Graduation requirement.'
        )

class NotificationAndPrereqTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_user(username='admin_test', password='password', role='admin')
        self.instructor = User.objects.create_user(username='instructor_test', password='password', role='instructor')
        self.student = User.objects.create_user(username='student_test', password='password', role='student')
        
        self.course_a = Course.objects.create(
            name='Course A',
            course_code='TEST101',
            seating_limit=10,
            instructor=self.instructor
        )
        
        self.course_b = Course.objects.create(
            name='Course B',
            course_code='TEST102',
            seating_limit=1,
            instructor=self.instructor
        )
        self.course_b.prerequisites.add(self.course_a)

    def test_prerequisite_enforcement(self):
        self.client.login(username='student_test', password='password')
        
        # Try to enroll in Course B without Course A
        response = self.client.post(reverse('enrollments:enroll_course', args=[self.course_b.id]))
        self.assertEqual(Enrollment.objects.filter(student=self.student).count(), 0)
        
        # Enroll in Course A
        Enrollment.objects.create(student=self.student, course=self.course_a)
        
        # Now try Course B again
        response = self.client.post(reverse('enrollments:enroll_course', args=[self.course_b.id]))
        self.assertEqual(Enrollment.objects.filter(student=self.student, course=self.course_b).count(), 1)

    def test_special_request_notification_to_instructor(self):
        self.client.login(username='student_test', password='password')
        
        # Submit request for Course B (missing prereq)
        response = self.client.post(
            reverse('enrollments:submit_enrollment_request', args=[self.course_b.id]),
            {'reason': 'I am smart'}
        )
        
        self.assertEqual(EnrollmentRequest.objects.count(), 1)
        req = EnrollmentRequest.objects.first()
        self.assertEqual(req.issue, 'prerequisites')
        
        # Check instructor notification
        self.assertEqual(Notification.objects.filter(user=self.instructor).count(), 1)
        notif = Notification.objects.filter(user=self.instructor).first()
        self.assertIn('special enrollment request', notif.message)
        self.assertIn('Missing Prerequisites', notif.message)

    def test_status_change_notification_to_student(self):
        req = EnrollmentRequest.objects.create(
            student=self.student,
            course=self.course_b,
            reason='Please',
            issue='full'
        )
        
        self.client.login(username='instructor_test', password='password')
        
        # Approve request
        response = self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course_b.id]),
            {'action': 'approve_request', 'request_id': req.id}
        )
        
        # Check student notification
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 1)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIn('APPROVED', notif.message)
        
        # Verify enrollment created
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course_b).exists())

    def test_waitlist_promotion_notification(self):
        # Fill Course B
        other_student = User.objects.create_user(username='other_student', password='password', role='student')
        Enrollment.objects.create(student=other_student, course=self.course_b)
        
        # Student joins waitlist
        Waitlist.objects.create(student=self.student, course=self.course_b)
        
        self.client.login(username='admin_test', password='password')
        
        # Remove other student to trigger promotion
        response = self.client.post(
            reverse('enrollments:manage_enrollment', args=[self.course_b.id]),
            {'action': 'remove', 'student_id': other_student.id}
        )
        
        # Check student notification
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 1)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIn('promoted from the waitlist', notif.message)
        
        # Verify enrollment created
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course_b).exists())



class RequestManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='password', role='admin')
        self.instructor = User.objects.create_user(username='instructor', password='password', role='instructor')
        self.student = User.objects.create_user(username='student', password='password', role='student')
        
        self.course = Course.objects.create(
            name='Test Course',
            course_code='TEST16',
            seating_limit=1,
            instructor=self.instructor
        )

    def test_pending_requests_displayed_on_management_page(self):
        req = EnrollmentRequest.objects.create(student=self.student, course=self.course, reason='Help', status='pending')
        
        self.client.login(username='instructor', password='password')
        response = self.client.get(reverse('enrollments:manage_enrollment', args=[self.course.id]))
        
        self.assertContains(response, 'student')
        self.assertContains(response, 'Help')

    def test_approve_enrollment_request(self):
        req = EnrollmentRequest.objects.create(student=self.student, course=self.course, status='pending')
        
        self.client.login(username='instructor', password='password')
        self.client.post(reverse('enrollments:manage_enrollment', args=[self.course.id]), {
            'action': 'approve_request',
            'request_id': req.id
        })
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_deny_enrollment_request(self):
        req = EnrollmentRequest.objects.create(student=self.student, course=self.course, status='pending')
        
        self.client.login(username='instructor', password='password')
        self.client.post(reverse('enrollments:manage_enrollment', args=[self.course.id]), {
            'action': 'deny_request',
            'request_id': req.id
        })
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'denied')
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_approve_request_overrides_seat_limit(self):
        # Fill the course first
        other_student = User.objects.create_user(username='other', password='password', role='student')
        Enrollment.objects.create(student=other_student, course=self.course)
        
        req = EnrollmentRequest.objects.create(student=self.student, course=self.course, status='pending')
        
        self.client.login(username='instructor', password='password')
        self.client.post(reverse('enrollments:manage_enrollment', args=[self.course.id]), {
            'action': 'approve_request',
            'request_id': req.id
        })
        
        # Should have 2 enrollments now, despite limit of 1
        self.assertEqual(Enrollment.objects.filter(course=self.course).count(), 2)

    def test_approve_request_prevents_duplicate_enrollment(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        req = EnrollmentRequest.objects.create(student=self.student, course=self.course, status='pending')
        
        self.client.login(username='instructor', password='password')
        self.client.post(reverse('enrollments:manage_enrollment', args=[self.course.id]), {
            'action': 'approve_request',
            'request_id': req.id
        })
        
        self.assertEqual(Enrollment.objects.filter(student=self.student, course=self.course).count(), 1)

    def test_cannot_reprocess_already_completed_request(self):
        req = EnrollmentRequest.objects.create(student=self.student, course=self.course, status='approved')
        
        self.client.login(username='instructor', password='password')
        response = self.client.post(reverse('enrollments:manage_enrollment', args=[self.course.id]), {
            'action': 'deny_request',
            'request_id': req.id
        }, follow=True)
        
        # Status should still be approved, not changed to denied
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.assertContains(response, 'This request has already been processed.')

    def test_student_sees_status_on_course_listing(self):
        # Test pending status
        EnrollmentRequest.objects.create(student=self.student, course=self.course, status='pending')
        self.client.login(username='student', password='password')
        response = self.client.get(reverse('course_list'))
        self.assertContains(response, 'Enrollment Request Submitted')
        
        # Test denied status
        EnrollmentRequest.objects.filter(student=self.student, course=self.course).update(status='denied')
        response = self.client.get(reverse('course_list'))
        self.assertContains(response, 'Denied')

class EnrollmentReportsTests(TestCase):

    def setUp(self):

        # Admin user
        self.admin = User.objects.create_user(
            username='admin1',
            password='password123',
            role='admin'
        )

        # Student user
        self.student = User.objects.create_user(
            username='student1',
            password='password123',
            role='student'
        )

        # Instructor user
        self.instructor = User.objects.create_user(
            username='instructor1',
            password='password123',
            role='instructor'
        )

        # Test course
        self.course = Course.objects.create(
            name='Algorithms',
            course_code='CS361',
            seating_limit=30,
            instructor=self.instructor
        )

        # Enrollment record
        Enrollment.objects.create(
            student=self.student,
            course=self.course
        )

    def test_admin_can_access_reports(self):
        """
        Verify admin can access reports page.
        """

        self.client.login(
            username='admin1',
            password='password123'
        )

        response = self.client.get(
            reverse('enrollments:enrollment_reports')
        )

        self.assertEqual(response.status_code, 200)

    def test_students_cannot_access_reports(self):
        """
        Verify students cannot access reports.
        """

        self.client.login(
            username='student1',
            password='password123'
        )

        response = self.client.get(
            reverse('enrollments:enrollment_reports')
        )

        self.assertEqual(response.status_code, 302)

    def test_report_displays_correct_enrollment_count(self):
        """
        Verify enrollment totals are correct.
        """

        self.client.login(
            username='admin1',
            password='password123'
        )
        response = self.client.get(reverse('enrollments:enrollment_reports'))
        self.assertContains(response, '3.3%')