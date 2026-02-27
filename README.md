# Institute Management System (IMS) - Minimal Tkinter App

A single-file Python application for managing students, teachers, and courses with SQLite persistence and a modern Tkinter UI.

Features:
- Add / Edit / Delete Students, Teachers, Courses
- Assign teachers to courses
- Enroll students in courses
- View reports: Students & enrollments, Teachers & courses, Courses & students
- SQLite database (`ims.db`) for persistence
- Clean & minimal Tkinter UI using ttk with sidebar navigation and header

Technology Stack:
- Python 3.x
- Tkinter + ttk for GUI
- SQLite for database
- Standard libraries only (no external dependencies)

Database Schema:
- `person`: id (PK), type ('student'/'teacher'), name, email, phone, extra
- `course`: id (PK), code (unique), title, duration, mode ('Online'/'Physical'/'Hybrid'), teacher_id (FK)
- `enrollment`: id (PK), student_id (FK), course_id (FK), unique(student_id, course_id)

Installation:
1. Make sure Python 3.x is installed.
2. Save file as `p3_ims.py`.
3. Run: `python p3_ims.py`

UI Overview:
- Header: Gradient-style top bar with title and subtitle
- Sidebar: Navigation to Dashboard, Students, Teachers, Courses, Reports
- Main Container: Loads selected page dynamically
- Pages:
  - Dashboard: Summary of students, teachers, courses
  - Students/Teachers: Forms for add/update/delete, list view, double-click to edit
  - Courses: Manage courses, assign teachers, view course list
  - Reports: Tabs showing Students & courses, Teachers & courses, Courses & students

Workflow:
1. Launch app → database auto-initializes (`ims.db`)
2. Use sidebar to navigate:
   - Add Students / Teachers via forms
   - Add Courses, then assign a teacher
   - Enroll students into courses
3. Use Reports to review all associations

Key Functions:
- `init_db()`: Initializes SQLite tables
- `add_person(type, name, email, phone, extra)`: Add student/teacher
- `update_person(id, name, email, phone, extra)`: Update record
- `delete_person(id)`: Delete student/teacher
- `add_course(code, title, duration, mode)`: Add course
- `update_course(id, code, title, duration, mode, teacher_id)`: Update course
- `delete_course(id)`: Delete course
- `assign_teacher_to_course(course_id, teacher_id)`: Assign teacher
- `enroll_student(student_id, course_id)`: Enroll student
- `get_people(type=None)`, `get_courses()`, `get_enrollments_by_course(course_id)`: Query helpers
