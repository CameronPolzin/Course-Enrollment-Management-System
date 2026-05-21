from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse



class RegistrationTests(TestCase):

    def test_register_valid_user(self):
        #AC1
        user = User.objects.create_user(
            username="testuser",
            password="password123",
            role="student"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "student")

    def test_register_duplicate_user(self):
        #AC2
        User.objects.create_user(
            username="duplicate",
            password="password123",
            role="student"
        )

        with self.assertRaises(Exception):
            User.objects.create_user(
                username="duplicate",
                password="password123",
                role="student"
            )

    def test_register_missing_fields(self):
        #AC3
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="",
                password="password123",
                role="student"
            )


class LoginTests(TestCase):

    def test_login_valid(self):
        #AC1
        User.objects.create_user(
            username="testuser",
            password="password123",
            role="student"
        )

        response = self.client.post("/login/", {
            "username": "testuser",
            "password": "password123"
        })

        self.assertEqual(response.status_code, 302)

    def test_login_invalid(self):
        #AC2
        response = self.client.post("/login/", {
            "username": "wrong",
            "password": "wrong"
        })

        self.assertEqual(response.status_code, 200)


class RoleTests(TestCase):

    def test_role_identified_on_login(self):
        #AC1
        user = User.objects.create_user(
            username="admin1",
            password="pass",
            role="admin"
        )

        self.client.login(username="admin1", password="pass")

        self.assertEqual(self.client.session['_auth_user_id'], str(user.id))
        self.assertEqual(user.role, "admin")
    
    def test_access_denied_for_wrong_role(self):
        #AC2
        user = User.objects.create_user(
            username="student1",
            password="pass",
            role="student"
        )
    
        self.client.login(username="student1", password="pass")
    
        response = self.client.get("/admin_dashboard/")
    
        self.assertEqual(response.status_code, 302)

    def test_access_granted_for_correct_role(self):
        #AC3
        user = User.objects.create_user(
            username="student2",
            password="pass",
            role="student"
        )

        self.client.login(username="student2", password="pass")

        response = self.client.get("/student_dashboard/")

        self.assertEqual(response.status_code, 200)


User = get_user_model()

class LogoutTests(TestCase):
    
    def test_logout_redirects_to_login(self):
        user = User.objects.create_user(
            username="testuser",
            password="pass",
            role="student"
        )

        self.client.login(username="testuser", password="pass")

        response = self.client.get('/logout/')

        self.assertRedirects(response, '/login/')


    def test_logout_blocks_protected_page(self):
        user = User.objects.create_user(
            username="testuser",
            password="pass",
            role="student"
        )

        self.client.login(username="testuser", password="pass")
        self.client.get('/logout/')

        response = self.client.get('/courses/')
        self.assertEqual(response.status_code, 302)  # redirected to login

class UserManagementTests(TestCase):
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

        self.client.login(username='admin', password='password123')

    def test_admin_view_user_list(self):
        """
        AC1: Given an authenticated admin, when the user list is accessed, all users are displayed.
        """
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('edit_users'))
        self.assertEqual(response.status_code, 200)
        # Verify all users created in setUp are in the context
        self.assertContains(response, self.admin_user.username)
        self.assertContains(response, self.instructor_user.username)
        self.assertContains(response, self.student_user.username)

    def test_admin_update_user_persistence(self):
        """
        AC2: Given user modifications are made, when changes are saved, updates persist.
        """
        self.client.login(username='admin', password='password123')
        # Assuming an 'update_user' URL exists or is handled by edit_users
        update_url = reverse('update_user', args=[self.student_user.id])
        data = {
            'username': 'student_updated',
            'role': 'instructor'
        }
        response = self.client.post(update_url, data)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.username, 'student_updated')
        self.assertEqual(self.student_user.role, 'instructor')

    def test_admin_can_change_user_password(self):
        """
        Verify that an admin can change another user's password and it persists.
        """
        self.client.login(username='admin', password='password123')
        update_url = reverse('update_user', args=[self.student_user.id])
        data = {
            'username': self.student_user.username,
            'role': self.student_user.role,
            'password': 'newpassword123'
        }
        response = self.client.post(update_url, data)
        self.student_user.refresh_from_db()
        
        # Verify the new password works
        login_success = self.client.login(username=self.student_user.username, password='newpassword123')
        self.assertTrue(login_success)


    def test_admin_delete_user(self):
        """
        AC3: Given a user is deleted, then the account is removed.
        """
        self.client.login(username='admin', password='password123')
        # Assuming a 'delete_user' URL exists
        delete_url = reverse('delete_user', args=[self.student_user.id])
        response = self.client.post(delete_url)
        
        user_exists = get_user_model().objects.filter(id=self.student_user.id).exists()
        self.assertFalse(user_exists)

    def test_non_admin_cannot_access_user_management(self):
        """
        Ensures instructors and students cannot access the user management pages.
        """
        # Test student
        self.client.login(username='student', password='password123')
        response = self.client.get(reverse('edit_users'))
        self.assertEqual(response.status_code, 302) # Redirected

        # Test instructor
        self.client.login(username='instructor', password='password123')
        response = self.client.get(reverse('edit_users'))
        self.assertEqual(response.status_code, 302) # Redirected

