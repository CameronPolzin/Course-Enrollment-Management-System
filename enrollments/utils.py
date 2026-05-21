from enrollments.models import Enrollment

def meets_prerequisites(student, course):
    """
    Checks if a student meets the prerequisites for a course.
    """
    prereqs = course.prerequisites.all()
    if not prereqs:
        return True

    # Get IDs of courses student is enrolled in
    enrolled_course_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)

    for prereq in prereqs:
        if prereq.id not in enrolled_course_ids:
            return False

    return True
