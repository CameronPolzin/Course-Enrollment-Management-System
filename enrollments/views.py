from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import EnrollmentRequestForm
from courses.models import Course
from .models import Enrollment, EnrollmentRequest, Waitlist
from notifications.models import Notification
from .utils import meets_prerequisites
from django.db.models import Count


@login_required
def enroll_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
        return redirect('course_list')

    if request.user.role != 'student':
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('course_list')

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You are already enrolled in this course.')
        return redirect('course_list')

    if course.is_full():
        messages.error(request, 'This course is already full.')
        return redirect('course_list')

    if not meets_prerequisites(request.user, course):
        messages.error(request, 'You do not meet the prerequisites for this course.')
        return redirect('course_list')

    Enrollment.objects.create(student=request.user, course=course)
    messages.success(request, 'You have successfully enrolled in the course.')
    return redirect('enrollments:my_enrollments') #go back to the courses page and display the courses user has enrolled

@login_required
def my_enrollments(request):
    if request.user.role != 'student':
        messages.error(request, 'Only students can view enrollments.')
        return redirect('course_list')

    enrollments = Enrollment.objects.filter(student=request.user)

    return render(request, 'enrollments/my_enrollments.html', {
        'enrollments': enrollments
    })


@login_required
def enrollment_history(request):
    if request.user.role != 'admin':
        messages.error(request, 'Sorry, only admins can access enrollment history.')
        return redirect('course_list')
    
    enrollments = Enrollment.objects.select_related('student','course').all().order_by('-enrolled_at')

    return render(request, 'enrollments/enrollment_history.html', {
        'enrollments':enrollments
    })
  
@login_required  
def drop_course(request, course_id):

    # Only students are allowed to drop courses
    if request.user.role != 'student':
        return redirect('course_list')  # unauthorized users redirected


        # Attempt to find the enrollment record for this student + course
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course_id=course_id
    )

    if request.method == "POST":
        course = enrollment.course
        # If found, delete the enrollment (drops the course)
        enrollment.delete()
        
        # Check waitlist
        promote_next_waitlisted_student(course)

        messages.success(request, "You have successfully dropped the course!")

        return redirect('enrollments:my_enrollments')


    # Redirect back to my Enrollments page after action
    return render(request,'enrollments/drop_course.html', {
        'enrollment': enrollment,
        'course': enrollment.course
    })

@login_required
def submit_enrollment_request(request, course_id):
    """
    Allows students to submit an enrollment request
    with a reason for special enrollment.
    """

    # Only students can submit requests
    if request.user.role != 'student':
        return redirect('course_list')

    # Find course or return error
    course = get_object_or_404(Course, id=course_id)

    # Prevent duplicate requests
    if EnrollmentRequest.objects.filter(
        student=request.user,
        course=course
    ).exists():

        messages.error(
            request,
            'You have already submitted a request for this course.'
        )

        return redirect('course_list')

    # Handle form submission
    if request.method == 'POST':

        # Create form with submitted data
        form = EnrollmentRequestForm(request.POST)

        if form.is_valid():

            # Create request object without saving yet
            enrollment_request = form.save(commit=False)

            # Attach student + course
            enrollment_request.student = request.user
            enrollment_request.course = course

            # Determine issue
            if course.is_full():
                enrollment_request.issue = 'full'
            elif not meets_prerequisites(request.user, course):
                enrollment_request.issue = 'prerequisites'

            # Save request
            enrollment_request.save()

            # Notify instructor
            if course.instructor:
                issue_display = dict(EnrollmentRequest.ISSUE_CHOICES).get(enrollment_request.issue, enrollment_request.issue)
                boilerplate = (
                    f"A student has submitted a special enrollment request for your course: {course.name} ({course.course_code}).\n"
                    f"Student: {request.user.get_full_name() or request.user.username}\n"
                    f"Issue: {issue_display}\n"
                    f"Reason: {enrollment_request.reason}"
                )
                Notification.notify(course.instructor, boilerplate)

            messages.success(
                request,
                'Enrollment request submitted successfully.'
            )

            return redirect('course_list')

    else:
        # Empty form on GET request
        form = EnrollmentRequestForm()

    # Render request form page
    return render(request,
                  'enrollments/submit_request.html',
                  {
                      'form': form,
                      'course': course
                  })


@login_required
def manage_enrollment(request, course_id):
    User = get_user_model()

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
        return redirect('course_list')

    if not (request.user.role == 'admin' or course.instructor == request.user):
        messages.error(request, 'You do not have permission to manage this course.')
        return redirect('course_list')

    students = User.objects.filter(role='student')
    enrollments = Enrollment.objects.filter(course=course)
    requests = EnrollmentRequest.objects.filter(course=course, status='pending')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            student_id = request.POST.get('student_id')
            try:
                student = User.objects.get(id=student_id, role='student')
            except User.DoesNotExist:
                messages.error(request, 'Student not found.')
                return redirect('enrollments:manage_enrollment', course_id=course.id)

            if Enrollment.objects.filter(student=student, course=course).exists():
                messages.error(request, 'Student is already enrolled in this course.')
            elif course.is_full():
                messages.error(request, 'This course is already full.')
            else:
                Enrollment.objects.create(student=student, course=course)
                messages.success(request, 'Student was added to the course.')

        elif action == 'remove':
            student_id = request.POST.get('student_id')
            try:
                student = User.objects.get(id=student_id, role='student')
            except User.DoesNotExist:
                messages.error(request, 'Student not found.')
                return redirect('enrollments:manage_enrollment', course_id=course.id)

            enrollment = Enrollment.objects.filter(student=student, course=course).first()

            if enrollment:
                enrollment.delete()
                promote_next_waitlisted_student(course)
                messages.success(request, 'Student was removed from the course.')
            else:
                messages.error(request, 'Student is not enrolled in this course.')
        
        elif action == 'approve_request' or action == 'deny_request':
            request_id = request.POST.get('request_id')
            enroll_request = get_object_or_404(EnrollmentRequest, id=request_id)
            
            if enroll_request.status != 'pending':
                messages.error(request, 'This request has already been processed.')
                return redirect('enrollments:manage_enrollment', course_id=course.id)
            
            if action == 'approve_request':
                enroll_request.status = 'approved'
                enroll_request.save()
                
                # Create enrollment
                Enrollment.objects.get_or_create(student=enroll_request.student, course=course)
                
                # Notify student
                Notification.notify(
                    enroll_request.student,
                    f"Your enrollment request for {course.name} ({course.course_code}) has been APPROVED. You are now enrolled!"
                )
                messages.success(request, f"Request for {enroll_request.student.username} approved.")
            else:
                enroll_request.status = 'denied'
                enroll_request.save()
                
                # Notify student
                Notification.notify(
                    enroll_request.student,
                    f"Your enrollment request for {course.name} ({course.course_code}) has been DENIED."
                )
                messages.success(request, f"Request for {enroll_request.student.username} denied.")

        return redirect('enrollments:manage_enrollment', course_id=course.id)

    return render(request, 'enrollments/manage_enrollment.html', {
        'course': course,
        'students': students,
        'enrollments': enrollments,
        'requests': requests
    })


#Waitlist
@login_required
def join_waitlist(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
        return redirect('course_list')

    if request.user.role != 'student':
        messages.error(request, 'Only students can join waitlists.')
        return redirect('course_list')

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You are already enrolled in this course.')
        return redirect('course_list')

    if Waitlist.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You are already on the waitlist for this course.')
        return redirect('course_list')

    if not course.is_full():
        messages.error(request, 'This course is not full. You can enroll instead.')
        return redirect('course_list')

    Waitlist.objects.create(student=request.user, course=course)
    messages.success(request, 'You have joined the waitlist for this course.')
    return redirect('course_list')


def promote_next_waitlisted_student(course):
    if course.is_full():
        return

    next_waitlist = Waitlist.objects.filter(course=course).order_by('joined_at').first()

    if next_waitlist:
        Enrollment.objects.create(
            student=next_waitlist.student,
            course=course
        )
        
        # Notify the student
        Notification.notify(
            next_waitlist.student,
            f"You have been promoted from the waitlist for {course.name} ({course.course_code}). You are now enrolled!"
        )
        
        next_waitlist.delete()

@login_required
def my_schedule(request):
    if request.user.role != 'student':
        messages.error(request, 'Only students can view enrollments.')
        return redirect('course_list')


    enrollments = Enrollment.objects.filter(student=request.user).select_related('course').order_by('course__start_time')


    return render(request, 'enrollments/my_schedule.html', {
        'enrollments': enrollments
    })

@login_required
def enrollment_reports(request):
    """
    Display enrollment reports and statistics.
    Only admins may access.
    """

    # Restrict access to admins only
    if request.user.role != 'admin':
        return redirect('course_list')

    # Get all courses
    courses = Course.objects.all()

    # Total enrollments across all courses
    total_enrollments = Enrollment.objects.count()

    # Build report data
    report_data = []

    for course in courses:

        # Number of enrolled students
        enrolled = course.enrollments.count()

        # Remaining seats
        remaining = course.seating_limit - enrolled

        # Seat usage percentage
        if course.seating_limit > 0:
            usage_percent = round(
                (enrolled / course.seating_limit) * 100,
                1
            )
        else:
            usage_percent = 0

        report_data.append({
            'course': course,
            'enrolled': enrolled,
            'remaining': remaining,
            'usage_percent': usage_percent,
        })

    return render(
        request,
        'enrollments/enrollment_reports.html',
        {
            'report_data': report_data,
            'total_enrollments': total_enrollments,
        }
    )

@login_required
def waitlist_status(request):
    if request.user.role != 'student':
        messages.error(request, 'Only students can view waitlist status.')
        return redirect('course_list')

    waitlist_records = Waitlist.objects.filter(
        student=request.user
    ).select_related('course').order_by('joined_at')

    waitlist_statuses = []

    for record in waitlist_records:
        position = Waitlist.objects.filter(
            course=record.course,
            joined_at__lte=record.joined_at
        ).count()

        waitlist_statuses.append({
            'course': record.course,
            'joined_at': record.joined_at,
            'position': position
        })

    return render(request, 'enrollments/waitlist_status.html', {
        'waitlist_statuses': waitlist_statuses
    })
