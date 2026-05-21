from django.core.management.base import BaseCommand
from users.models import User
from courses.models import Course
import random


FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William",
    "David", "Joseph", "Thomas", "Charles", "Daniel",
    "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Edward", "Ronald", "Timothy",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Gary"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

COURSES = [
    ("CS101", "Intro to Programming"),
    ("CS102", "Python Fundamentals"),
    ("CS201", "Data Structures"),
    ("CS202", "Computer Architecture"),
    ("CS240", "Discrete Mathematics"),
    ("CS301", "Algorithms"),
    ("CS315", "Operating Systems"),
    ("CS320", "Database Systems"),
    ("CS330", "Software Engineering"),
    ("CS337", "Systems Programming"),
    ("CS340", "Computer Networks"),
    ("CS350", "Cybersecurity"),
    ("CS360", "Artificial Intelligence"),
    ("CS370", "Machine Learning"),
    ("CS380", "Web Development"),
]


class Command(BaseCommand):
    help = "Seeds demo users, courses, and enrollments"

    def create_random_user(self, username, role):
        if User.objects.filter(username=username).exists():
            return

        User.objects.create_user(
            username=username,
            password="password",
            role=role,
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
        )

    def handle(self, *args, **kwargs):
        # =========================
        # GUARANTEED DEMO ACCOUNTS
        # =========================

        demo_accounts = [
            ("admin", "admin"),
            ("instructor", "instructor"),
            ("student", "student"),
        ]

        for username, role in demo_accounts:

            if not User.objects.filter(username=username).exists():

                User.objects.create_user(
                    username=username,
                    password=username,   # password matches username
                    role=role,
                    first_name=role.upper(),
                    last_name="DEMO"
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created demo account: {username}/{username}"
                    )
                )
        # =========================
        # CREATE ADMINS
        # =========================
        for i in range(1, 4):
            self.create_random_user(
                f"admin{i:03}",
                "admin"
            )
            self.stdout.write(
                    self.style.SUCCESS(
                        f"Created Admin account: {username}/{username}"
                    )
                )

        # =========================
        # CREATE INSTRUCTORS
        # =========================
        for i in range(1, 11):
            self.create_random_user(
                f"instructor{i:03}",
                "instructor"
            )
            self.stdout.write(
                    self.style.SUCCESS(
                        f"Created Instructor account: {username}/{username}"
                    )
                )

        # =========================
        # CREATE STUDENTS
        # =========================
        for i in range(1, 31):
            self.create_random_user(
                f"student{i:03}",
                "student"
            )
            self.stdout.write(
                    self.style.SUCCESS(
                        f"Created Student account: {username}/{username}"
                    )
                )

        instructors = list(
            User.objects.filter(role="instructor")
            .exclude(username="instructor")
        )

        # =========================
        # CREATE COURSES
        # =========================
        created_courses = []

        for code, name in COURSES:

            start_hour = random.choice([
                8, 9, 10, 11, 12, 13, 14, 15, 16
            ])

            start_time = f"{start_hour:02}:00"

            # class lasts 1 hour 15 mins
            end_hour = start_hour + 1
            end_time = f"{end_hour:02}:15"

            course, created = Course.objects.get_or_create(
                course_code=code,
                defaults={
                    "name": name,
                    "description": f"{name} course description",
                    "seating_limit": random.choice([
                        10,
                        15,
                        20,
                        25,
                        30
                    ]),
                    "start_time": start_time,
                    "end_time": end_time,
                    "instructor": random.choice(instructors),
                }
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created course: {course.course_code} - {course.name}"
                )
            )
            created_courses.append(course)

        # =========================
        # ADD PREREQUISITES
        # =========================
        for course in created_courses:

            possible_prereqs = [
                c for c in created_courses
                if c != course
            ]

            prereq_count = random.randint(0, 2)

            prereqs = random.sample(
                possible_prereqs,
                prereq_count
            )

            course.prerequisites.set(prereqs)

        self.stdout.write(
            self.style.SUCCESS(
                "User and Course data seeded successfully!"
            )
        )

        # =========================
        # CREATE ENROLLMENTS
        # =========================

        from enrollments.models import Enrollment

        students = list(
            User.objects.filter(role="student")
            .exclude(username="student")
        )

        # Random enrollments
        for student in students:

            # each student gets 2-5 random courses
            random_courses = random.sample(
                created_courses,
                random.randint(2, 5)
            )

            for course in random_courses:

                # prevent duplicate enrollments
                if not Enrollment.objects.filter(
                    student=student,
                    course=course
                ).exists():

                    Enrollment.objects.create(
                        student=student,
                        course=course
                    )

        # =========================
        # FORCE SOME COURSES FULL
        # =========================

        # pick 3 random courses to become full
        full_courses = random.sample(
            created_courses,
            3
        )

        for course in full_courses:

            # clear current enrollments
            course.enrollments.all().delete()

            # choose enough students to fill course
            selected_students = random.sample(
                students,
                min(course.seating_limit, len(students))
            )

            for student in selected_students:

                Enrollment.objects.create(
                    student=student,
                    course=course
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{course.course_code} is now FULL"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Enrollments created successfully!"
            )
        )