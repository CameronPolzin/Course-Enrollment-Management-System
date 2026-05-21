# Course Enrollment Management System

A full-stack web application developed using Django for managing university course enrollment workflows. This project was completed as part of a Software Engineering group project using Agile/Scrum methodologies.

## Project Overview

The Course Enrollment Management System allows students, instructors, and administrators to manage course enrollment operations through a centralized web portal.

The system supports:
- User authentication and role-based access control
- Course creation and management
- Student enrollment workflows
- Waitlists and special enrollment requests
- Enrollment history tracking
- Advanced course search and filtering
- Notifications and request management

---

# My Contributions

## Backend Development
- Implemented user authentication and role-based access control for students, instructors, and admins
- Developed enrollment workflows including:
  - standard enrollment
  - waitlists
  - special enrollment requests
  - prerequisite validation
  - duplicate enrollment prevention
- Built course management features including:
  - course creation
  - course editing
  - course detail pages
  - schedule viewing
  - enrollment history

## Frontend / UI Development
- Designed and styled reusable Django templates and shared CSS layouts
- Implemented a shared `base.html` layout for consistent navigation/UI
- Improved usability through:
  - centered responsive forms
  - reusable form layouts
  - improved navigation
  - cleaner course detail pages
  - improved schedule viewer

## Search & Filtering Features
- Implemented advanced course filtering by:
  - instructor
  - availability
  - start/end time
  - prerequisites
- Added partial instructor name searching

## Testing & Quality Assurance
- Wrote and maintained unit and acceptance tests
- Performed regression testing during sprint development
- Helped debug authentication and enrollment edge cases

## Software Engineering Contributions
- Created and refined PBIs, user stories, and acceptance criteria
- Contributed to UML diagrams, state diagrams, and design documentation
- Participated in Scrum meetings and sprint planning
- Applied Agile development practices and SOLID design principles

---

# Technologies Used

- Python
- Django
- HTML
- CSS
- SQLite
- Git/GitHub

---

# Features

## Student Features
- Register/Login
- Browse courses
- Search and filter courses
- Enroll in courses
- Submit enrollment requests
- Join waitlists
- View personal schedule
- View notifications

## Instructor Features
- Manage assigned courses
- View enrolled students
- Approve/Deny enrollment requests
- Edit course information
- Send Notifications

## Admin Features
- Create/Edit/Delete courses
- Manage users
- View enrollment history
- Manage all enrollments
- Send Notifications

---

# Development Process

This project was developed using Agile/Scrum practices across multiple sprints. Features were implemented incrementally with:
- Product Backlogs
- Sprint Planning
- Scrum Meetings
- UML Design Diagrams
- Unit Testing
- Acceptance Testing

---

# Lessons Learned

- Importance of incremental Agile development
- Writing reusable and maintainable code
- Applying SOLID design principles
- Managing GitHub collaboration and merge conflicts
- Importance of testing and regression prevention

---

# Disclaimer

This repository is a personal showcase copy of a university group project. The project was originally completed collaboratively as part of a Software Engineering course, and not all the code is mine.

--- 

# How to Run the Project

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-folder>
```


## 2. Create a Virtual Environment

### Windows
```bash
python -m venv venv
```

### Mac/Linux
```bash
python3 -m venv venv
```


## 3. Activate the Virtual Environment

### Windows
```bash
venv\Scripts\activate
```

### Mac/Linux
```bash
source venv/bin/activate
```


## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not included:

```bash
pip install django
```


## 5. Apply Database Migrations

```bash
python manage.py migrate
```


## 6. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.


## 7. Run the Development Server

```bash
python manage.py runserver
```


## 8. Open the Application

Open your browser and go to:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

# Running Tests

Run all unit tests:

```bash
python manage.py test
```

# Demo Accounts (Optional)

Example accounts used during development:

```text
Admin:
Username: admin
Password: admin

Instructor:
Username: instructor
Password: instructor

Student:
Username: student
Password: student
```
