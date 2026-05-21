from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Course
from django.db import IntegrityError

User = get_user_model()

class CourseManagementTests(TestCase):
    def setUp(self):
        # Setup users for permission testing using project-specific role field
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@uwm.edu',
            password='password123',
            role='admin'
        )
        self.instructor_user = User.objects.create_user(
            username='instructor',
            password='password123',
            role='instructor',
        )
        self.other_instructor_user = User.objects.create_user(
            username='other_instructor',
            password='password123',
            role='instructor',
        )
        self.student_user = User.objects.create_user(
            username='student',
            password='password123',
            role='student',
        )

        self.course = Course.objects.create(
            course_code="CS361",
            name="Software Engineering",
            description="Introduction to software development lifecycles.",
            instructor=self.instructor_user,
        )
    def test_course_creation(self):
        """Verify course is created with correct identification and naming."""
        self.assertEqual(self.course.course_code, "CS361")
        self.assertEqual(self.course.name, "Software Engineering")

    def test_string_representation(self):
        """String representation"""
        self.assertEqual(str(self.course),self.course.course_code + " - " + self.course.name)
        
    def test_course_code_uniqueness(self):
        """If a duplicate course register attempt is made it should fail."""
        with self.assertRaises(IntegrityError):
            Course.objects.create(
                course_code="CS361",
                name="Duplicate Course",
                description="This should fail."
            )
    def test_nonexistent_course_redirect(self):
        """Verify that a link which does not exist does not pass"""
        response = self.client.get('/courses_bad_url_xylophone/')
        self.assertEqual(response.status_code, 404)
    def test_course_list_access_admin(self):
        """Verify course list is accessible."""
        self.client.login(username='admin', password='password123')
        response = self.client.get('/courses/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS361")

    def test_course_list_access_instructor(self):
        """Verify course list is accessible."""
        self.client.login(username='instructor', password='password123')
        response = self.client.get('/courses/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS361")

    def test_course_list_access_student(self):
        """Verify course list is accessible."""
        self.client.login(username='student', password='password123')
        response = self.client.get('/courses/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS361")
    def test_course_create_access_admin(self):
        """Verify course creator is accessible."""
        self.client.login(username='admin', password='password123')
        response = self.client.get('/courses/create/')
        self.assertEqual(response.status_code, 200)
    def test_course_create_access_instructor(self):
        """Verify course list is inaccessible."""
        self.client.login(username='instructor', password='password123')
        response = self.client.get('/courses/create/')
        self.assertEqual(response.status_code, 403)

    def test_course_create_access_student(self):
        """Verify course list is inaccessible."""
        self.client.login(username='student', password='password123')
        response = self.client.get('/courses/create/')
        self.assertEqual(response.status_code, 403)


class CourseEditTests(TestCase):
    def setUp(self):
        # Setup users for permission testing using project-specific role field
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@uwm.edu',
            password='password123',
            role='admin'
        )
        self.instructor_user = User.objects.create_user(
            username='instructor',
            password='password123',
            role='instructor',
        )
        self.other_instructor_user = User.objects.create_user(
            username='other_instructor',
            password='password123',
            role='instructor',
        )
        self.student_user = User.objects.create_user(
            username='student',
            password='password123',
            role='student',
        )

        self.course = Course.objects.create(
            course_code="CS361",
            name="Software Engineering",
            description="Introduction to software development lifecycles.",
            instructor=self.instructor_user,
        )
        self.other_course = Course.objects.create(
            course_code="CS351",
            name="Algorithms and Data Structures",
            description="Programming in a structured, high-level, object-oriented language. Implementation of data structures and algorithms and their application.",
            instructor=self.instructor_user,
        )

    def test_edit_course_success_assigned_instructor(self):
        """
        Given an authenticated instructor is logged in
        And assigned to a course
        When course details are updated
        Then the changes are saved and reflected in the system
        """
        self.client.login(username='instructor', password='password123')
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'description': 'Updated description.',
            'seating_limit': 50,
            'start_time': '10:00',
            'end_time': '11:00'
        })
        self.assertEqual(response.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.description, 'Updated description.')
        self.assertEqual(self.course.seating_limit, 50)
        self.assertEqual(self.course.course_schedule(), 'Mon-Thu 10:00 - 11:00')

    def test_edit_course_success_admin(self):
        """
        Given an authenticated instructor is logged in
        And assigned to a course
        When course details are updated
        Then the changes are saved and reflected in the system
        """
        self.client.login(username='admin', password='password123')
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'description': 'Updated description.',
            'seating_limit': 50,
            'start_time': '10:00',
            'end_time': '11:00',
            'name': 'Different',
            'course_code': 'CS362',
            'instructor': self.other_instructor_user.id,
            'prerequisites': [self.other_course.id],
        })
        self.assertEqual(response.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.description, 'Updated description.')
        self.assertEqual(self.course.seating_limit, 50)
        self.assertEqual(self.course.course_schedule(), 'Mon-Thu 10:00 - 11:00')

    def test_edit_course_denied_unassigned_instructor(self):
        """
        Given an authenticated instructor is logged in
        And they are not assigned to the course
        When an update is attempted
        Then access is denied
        """
        self.client.login(username='other_instructor', password='password123')
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'description': 'Instructor2 hacked description.',
            'seating_limit': 100,
        })
        self.assertEqual(response.status_code, 403)
        self.course.refresh_from_db()
        self.assertNotEqual(self.course.description, 'Instructor2 hacked description.')

    def test_edit_course_denied_student(self):
        """
        Given an authenticated instructor is logged in
        And they are not assigned to the course
        When an update is attempted
        Then access is denied
        """
        self.client.login(username='student', password='password123')
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'description': 'Student hacked description.',
            'seating_limit': 100,
        })
        self.assertEqual(response.status_code, 403)
        self.course.refresh_from_db()
        self.assertNotEqual(self.course.description, 'Student hacked description.')


class CourseSearchFilterTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='student',
            password='pass',
            role='student'
        )

        self.instructor = User.objects.create_user(
            username='prof1',
            password='pass',
            role='instructor'
        )

        self.course1 = Course.objects.create(
            course_code='CS101',
            name='Intro to CS',
            instructor=self.instructor,
            seating_limit=2
        )

        self.course2 = Course.objects.create(
            course_code='MATH200',
            name='Calculus',
            instructor=self.instructor,
            seating_limit=2
        )

        self.client.login(username='student', password='pass')
    
    def test_search_by_name(self):
        response = self.client.get(reverse('course_list') + '?q=Intro')

        self.assertContains(response, 'Intro to CS')
        self.assertNotContains(response, 'Calculus')

    def test_search_by_course_code(self):
        response = self.client.get(reverse('course_list') + '?q=CS101')

        self.assertContains(response, 'CS101')
        self.assertNotContains(response, 'MATH200')

    def test_filter_by_instructor(self):
        response = self.client.get(reverse('course_list') + '?instructor=prof1')

        self.assertContains(response, 'CS101')
        self.assertContains(response, 'MATH200')

    def test_filter_available_only(self):
    # simulate course1 being full
        from enrollments.models import Enrollment
        Enrollment.objects.create(student=self.user, course=self.course1)
        Enrollment.objects.create(student=self.instructor, course=self.course1)

        response = self.client.get(reverse('course_list') + '?available=1')

        self.assertNotContains(response, 'CS101')  # full
        self.assertContains(response, 'MATH200')   # not full

    def test_search_and_filter_combined(self):
        response = self.client.get(reverse('course_list') + '?q=CS&instructor=prof1')

        self.assertContains(response, 'CS101')
        self.assertNotContains(response, 'MATH200')

    def test_no_results(self):
        response = self.client.get(reverse('course_list') + '?q=NONEXISTENT')

        self.assertContains(response, 'No Courses Found.')


class CourseListDropdownTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password123',
            role='admin'
        )
        self.instructor_user = User.objects.create_user(
            username='instructor',
            password='password123',
            role='instructor',
        )
        self.other_instructor_user = User.objects.create_user(
            username='instructor2',
            password='password123',
            role='instructor',
        )
        self.student_user = User.objects.create_user(
            username='student_user',
            password='password123',
            first_name='John',
            last_name='Doe',
            role='student'
        )
        self.other_student_user = User.objects.create_user(
            username='student_user2',
            password='password123',
            first_name='Jane',
            last_name='Doe',
            role='student'
        )
        self.course1 = Course.objects.create(
            course_code="CS361",
            name="Software Engineering",
            instructor=self.instructor_user,
        )
        self.course2 = Course.objects.create(
            course_code="CS351",
            name="Data Structures",
            instructor=self.other_instructor_user,
        )

    def test_course_list_view_with_enrolled_student_as_instructor(self):
        from enrollments.models import Enrollment
        Enrollment.objects.create(student=self.student_user, course=self.course1)

        self.client.login(username='instructor', password='password123')
        response = self.client.get(reverse('course_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Engineering')
        self.assertContains(response, 'CS361')
        self.assertContains(response, 'View Students')
        self.assertContains(response, 'John Doe')

    def test_course_list_view_with_wrong_enrolled_student_as_instructor(self):
        # Student enrolled in instructor's course, other student enrolled in other instructor's course
        from enrollments.models import Enrollment
        Enrollment.objects.create(student=self.student_user, course=self.course1)
        Enrollment.objects.create(student=self.other_student_user, course=self.course2)

        self.client.login(username='instructor', password='password123')
        response = self.client.get(reverse('course_list'))

        self.assertEqual(response.status_code, 200)
        # Should see John Doe in their own course
        self.assertContains(response, 'John Doe')
        # Should NOT see Jane Doe because she's in a different instructor's course
        self.assertNotContains(response, 'Jane Doe')

    def test_course_list_view_no_students_enrolled_as_instructor(self):
        self.client.login(username='instructor', password='password123')
        response = self.client.get(reverse('course_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No students enrolled.')

    def test_course_list_view_as_admin(self):
        from enrollments.models import Enrollment
        Enrollment.objects.create(student=self.student_user, course=self.course1)
        Enrollment.objects.create(student=self.other_student_user, course=self.course2)

        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('course_list'))

        self.assertEqual(response.status_code, 200)
        # Admin sees both enrollments
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Jane Doe')
        self.assertContains(response, 'View Students', count=2)

    def test_course_list_view_as_student(self):
        self.client.login(username='student_user', password='password123')
        response = self.client.get(reverse('course_list'))

        self.assertEqual(response.status_code, 200)
        # Student sees no dropdowns
        self.assertNotContains(response, 'View Students')