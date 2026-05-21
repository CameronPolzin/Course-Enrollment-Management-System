from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import CourseForm, InstructorCourseForm
from .models import Course, TIME_CHOICES
from enrollments.models import Enrollment, EnrollmentRequest, Waitlist
from enrollments.utils import meets_prerequisites
from django.db.models import Q

@login_required
def create_course(request):
    """
    Handles the creation of new course records.
    Restricts access to staff, superusers, or users with the 'admin' role.
    Processes POST data via CourseForm and redirects to the course list upon success.
    """
    if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'admin'):
        raise PermissionDenied

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm()

    return render(request, 'courses/create_course.html', {'form': form})



def promote_waitlisted_students_for_course(course):
    while not course.is_full():
        next_waitlist = Waitlist.objects.filter(course=course).order_by('joined_at').first()

        if not next_waitlist:
            break

        if not Enrollment.objects.filter(student=next_waitlist.student, course=course).exists():
            Enrollment.objects.create(
                student=next_waitlist.student,
                course=course
            )
            
            # Notify the student
            from notifications.models import Notification
            Notification.notify(
                next_waitlist.student,
                f"You have been promoted from the waitlist for {course.name} ({course.course_code}). You are now enrolled!"
            )

        next_waitlist.delete()


@login_required
def course_list(request):
    """
    Retrieves and displays all existing courses.
    and orders results alphabetically by course code.
    """
    courses = Course.objects.select_related('instructor').prefetch_related('enrollments__student').all().order_by('course_code')
    
    #FILTER: search query
    query = request.GET.get('q')
    if query:
        courses = courses.filter(
            Q(course_code__icontains=query) |
            Q(name__icontains=query)
        )

    #FILTER: by instructor username
    # Instructor search
    instructor = request.GET.get('instructor')

    if instructor:

        courses = courses.filter(

            Q(instructor__username__icontains=instructor) |

            Q(instructor__first_name__icontains=instructor) |

            Q(instructor__last_name__icontains=instructor)

        )

    #FILTER: by time slot
    start_time = request.GET.get('start_time')

    if start_time:
        courses = courses.filter(
            start_time__gte=start_time
        )

    # Filter by end time
    end_time = request.GET.get('end_time')

    if end_time:
        courses = courses.filter(
            end_time__lte=end_time
        )

    #FILTER: available only
    available = request.GET.get('available')
    if available:
        courses = [c for c in courses if not c.is_full()]
        
    # FILTER: missing prerequisites
    has_prereqs = request.GET.get('has_prereqs')
    if has_prereqs == 'yes':
        courses = courses.filter(
            prerequisites__isnull=False
        ).distinct()

    elif has_prereqs == 'no':

        courses = courses.filter(
            prerequisites__isnull=True
        )
        
    #ORDER LAST
    courses = sorted(courses, key=lambda x: x.course_code)   

    for course in courses:
        promote_waitlisted_students_for_course(course)

    enrolled_course_ids = []

    requested_course_ids = []

    waitlisted_course_ids = []

    if request.user.role == 'student':
        enrolled_course_ids = Enrollment.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)

    # Get courses that already have submitted requests
    requested_course_ids = []
    denied_course_ids = []
    
    if request.user.role == 'student':
        requested_course_ids = EnrollmentRequest.objects.filter(
            student=request.user,
            status='pending'
        ).values_list('course_id', flat=True)
        
        denied_course_ids = EnrollmentRequest.objects.filter(
            student=request.user,
            status='denied'
        ).values_list('course_id', flat=True)

    #Waitlist

    waitlisted_course_ids = Waitlist.objects.filter(student=request.user).values_list('course_id', flat=True)

    courses_missing_prereqs = []
    if request.user.role == 'student':
        for course in courses:
            if not meets_prerequisites(request.user, course):
                courses_missing_prereqs.append(course.id)


    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'enrolled_course_ids': enrolled_course_ids,
        'requested_course_ids': requested_course_ids,
        'denied_course_ids': denied_course_ids,
        'waitlisted_course_ids': waitlisted_course_ids,
        'courses_missing_prereqs': courses_missing_prereqs,
        'time_choices': TIME_CHOICES,
    })

@login_required
def edit_course(request, course_id):

    # fetch course or 404
    course = get_object_or_404(Course, id=course_id)

    # permission check: only admin or course instructor can edit
    if not (request.user.role == 'admin' or course.instructor == request.user):
        raise PermissionDenied

    #dynamically create form class based on user role
    if request.user.role == 'admin':
        form_class = CourseForm
    else:
        form_class = InstructorCourseForm

    # handle form submission
    if request.method == 'POST':
        form = form_class(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = form_class(instance=course)

    return render(request, 'courses/edit_course.html', {
        'form': form,
        'course': course
    })

def course_detail(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    return render(
        request,
        'courses/course_detail.html',
        {
            'course': course
        }
    )