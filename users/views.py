from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model


def home(request):
    '''
    Renders the home page and redirects authenticated users to their respective dashboards based on their roles
    '''
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('/admin_dashboard/')
        elif request.user.role == 'instructor':
            return redirect('/instructor_dashboard/')
        else:
            return redirect('/student_dashboard/')
    return render(request, "users/home.html")

def register(request):
    '''
    Handles user registration.

    GET request:
    Displays empty registration form.

    POST request:
    Validates form and creates user.
    '''
    success = None
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            success = 'Account created successfully.'
            # Reset form after successful registration
            form = UserRegistrationForm()
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {
        'form': form,
        'success': success
    })

def user_login(request):
    '''
    Handles user login and authentication

    GET request: Displays the login form

    POST request: Validates the submitted credentials, creates a session for the user if valid, and redirects to the 
                  appropriate dashboard based on their role. If invalid, displays an error message
    '''
    error = "" #initialize error message variable

    if request.method == 'POST':
        username = request.POST.get('username') #get username from submitted form data
        password = request.POST.get('password') #get password from submitted form data

        #check credentials
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user) #creates session for user
            
            #role redirect
            #send user to appropriate dashboard based on their role
            if user.role == 'admin':
                return redirect('/admin_dashboard/')
            elif user.role == 'instructor':
                return redirect('/instructor_dashboard/')
            else:
                return redirect('/student_dashboard/')

        else:
            #invalid credentials, set error message to display on login page
            error = "Invalid username or password"

    return render(request, 'users/login.html', {'error': error})


def user_logout(request):
    '''
    Handles user logout by clearing the session and redirecting to the login page
    '''
    logout(request) #removes session
    return redirect('login') #redirect to login page


@login_required #checks if user is logged in, if not redirects to login page
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('/login/')
    return render(request, 'users/admin_dashboard.html')

@login_required #checks if user is logged in, if not redirects to login page
def instructor_dashboard(request):
    if request.user.role != 'instructor':
        return redirect('/login/')
    return render(request, 'users/instructor_dashboard.html')

@login_required #checks if user is logged in, if not redirects to login page    
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('/login/')
    return render(request, 'users/student_dashboard.html')

@login_required
def edit_users(request):
    if request.user.role != 'admin':
        return redirect('/home/')
    users = get_user_model().objects.all()
    return render(request, 'users/edit_users.html', {'users': users})

@login_required
def update_user(request, user_id):
    """
    Handles user account updates (username, role, and password).
    """
    if request.user.role != 'admin':
        return redirect('/home/')
    
    user_to_edit = get_object_or_404(get_user_model(), id=user_id)
    
    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_role = request.POST.get('role')
        new_password = request.POST.get('password')
        
        if new_username:
            user_to_edit.username = new_username
        if new_role:
            user_to_edit.role = new_role
        if new_password:
            user_to_edit.set_password(new_password)
            
        user_to_edit.save()
        return redirect('edit_users')
        
    return redirect('edit_users')

@login_required
def delete_user(request, user_id):
    """
    Handles user account deletion.
    """
    if request.user.role != 'admin':
        return redirect('/home/')
        
    user_to_delete = get_object_or_404(get_user_model(), id=user_id)
    
    if request.method == 'POST':
        user_to_delete.delete()
        
    return redirect('edit_users')
