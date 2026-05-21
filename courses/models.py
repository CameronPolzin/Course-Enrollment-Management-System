from django.db import models
from django.conf import settings

# Generate 15-minute interval choices
TIME_CHOICES = []

for hour in range(24):
    for minute in range(0, 60, 15):

        # Format hour/minute nicely
        time_value = f"{hour:02}:{minute:02}"

        # Add tuple for dropdown
        TIME_CHOICES.append(
            (time_value, time_value)
        )
        
class Course(models.Model):
    name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    # Course start time
    start_time = models.CharField(
        max_length=5,
        choices=TIME_CHOICES,
        blank=True
    )

    # Course end time
    end_time = models.CharField(
        max_length=5,
        choices=TIME_CHOICES,
        blank=True
    )
    
    seating_limit = models.IntegerField(default=1)

    instructor = models.ForeignKey( #allows you to select from registered instructors during class creation
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught',
        limit_choices_to={'role': 'instructor'},
    )
    prerequisites = models.ManyToManyField(
    'self',
    symmetrical=False,
    blank=True
    )

    def is_full(self):
        return self.enrollments.count() >= self.seating_limit
    
    def seats_taken(self):
        return self.enrollments.count()
    
    def seats_display(self):
        return f"{self.seats_taken()}/{self.seating_limit}"
    
    def course_schedule(self):
        """
        Returns formatted schedule string.
        Example: Mon-Thu 09:00 - 10:15
        """
        return f"Mon-Thu {self.start_time} - {self.end_time}"

    def __str__(self):
        return f"{self.course_code} - {self.name}"