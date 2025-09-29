"""
p3_ims.py - Institute Management System (single-file)
Save as p3_ims.py and run: python p3_ims.py

Features:
- Student / Teacher / Course management (Add / Edit / Delete)
- Assign teacher to course
- Enroll students in courses
- Reports view
- SQLite persistence (ims.db)
- Minimal & modern Tkinter UI using ttk
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

DB = "ims.db"


# ---------- Database helpers ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS person (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- 'student' or 'teacher'
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        extra TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS course (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        title TEXT NOT NULL,
        duration TEXT,
        mode TEXT, -- online/physical
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES person(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        UNIQUE(student_id, course_id),
        FOREIGN KEY (student_id) REFERENCES person(id),
        FOREIGN KEY (course_id) REFERENCES course(id)
    )""")
    conn.commit()
    conn.close()


def query(sql, params=(), fetch=False, many=False):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if many:
        c.executemany(sql, params)
        conn.commit()
        conn.close()
        return None
    c.execute(sql, params)
    if fetch:
        res = c.fetchall()
        conn.close()
        return res
    conn.commit()
    conn.close()


# ---------- Models (lightweight) ----------
def add_person(p_type, name, email="", phone="", extra=""):
    query(
        "INSERT INTO person(type,name,email,phone,extra) VALUES(?,?,?,?,?)",
        (p_type, name, email, phone, extra),
    )


def update_person(person_id, name, email, phone, extra):
    query(
        "UPDATE person SET name=?, email=?, phone=?, extra=? WHERE id=?",
        (name, email, phone, extra, person_id),
    )


def delete_person(person_id):
    query("DELETE FROM person WHERE id=?", (person_id,))


def get_people(p_type=None):
    if p_type:
        return query("SELECT id,name,email,phone,extra FROM person WHERE type=? ORDER BY name", (p_type,), fetch=True)
    return query("SELECT id,type,name,email,phone,extra FROM person ORDER BY type, name", fetch=True)


def add_course(code, title, duration, mode):
    query("INSERT INTO course(code,title,duration,mode) VALUES(?,?,?,?)", (code, title, duration, mode))


def update_course(cid, code, title, duration, mode, teacher_id=None):
    query("UPDATE course SET code=?, title=?, duration=?, mode=?, teacher_id=? WHERE id=?",
          (code, title, duration, mode, teacher_id, cid))


def delete_course(cid):
    query("DELETE FROM course WHERE id=?", (cid,))


def get_courses():
    return query("SELECT id, code, title, duration, mode, teacher_id FROM course ORDER BY title", fetch=True)


def assign_teacher_to_course(course_id, teacher_id):
    query("UPDATE course SET teacher_id=? WHERE id=?", (teacher_id, course_id))


def enroll_student(student_id, course_id):
    try:
        query("INSERT INTO enrollment(student_id, course_id) VALUES(?,?)", (student_id, course_id))
        return True
    except sqlite3.IntegrityError:
        return False


def unenroll_student(student_id, course_id):
    query("DELETE FROM enrollment WHERE student_id=? AND course_id=?", (student_id, course_id))


def get_enrollments_by_course(course_id):
    return query("""SELECT p.id, p.name FROM enrollment e
                    JOIN person p ON e.student_id = p.id
                    WHERE e.course_id = ? ORDER BY p.name""", (course_id,), fetch=True)


def get_courses_with_students():
    return query("""SELECT c.id, c.code, c.title, p.id, p.name
                    FROM course c
                    LEFT JOIN enrollment e ON c.id = e.course_id
                    LEFT JOIN person p ON e.student_id = p.id
                    ORDER BY c.title""", fetch=True)


def get_teachers_with_courses():
    return query("""SELECT t.id, t.name, c.id, c.code, c.title
                    FROM person t
                    LEFT JOIN course c ON t.id = c.teacher_id
                    WHERE t.type='teacher'
                    ORDER BY t.name""", fetch=True)


# ---------- UI Components ----------
class IMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Institute Management System - Minimal IMS")
        self.geometry("980x640")
        self.minsize(900, 580)

        # style
        self.style = ttk.Style(self)
        self._set_style()

        # main layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_header()
        self._create_sidebar()
        self._create_main_container()

        # frames container for pages
        self.frames = {}
        for F in (DashboardPage, StudentsPage, TeachersPage, CoursesPage, ReportsPage):
            page = F(self.main_container, self)
            self.frames[F.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")

        # show Students by default
        self.show_frame("DashboardPage")

    def _set_style(self):
        # Basic modern ttk style adjustments
        default_font = ("Inter", 11)
        self.style.configure("TLabel", font=default_font)
        self.style.configure("TButton", font=default_font, padding=6)
        self.style.configure("Header.TLabel", font=("Inter", 16, "bold"))
        self.style.configure("Accent.TButton", foreground="white")
        try:
            self.style.configure("Treeview", rowheight=26, font=default_font)
            self.style.configure("Treeview.Heading", font=("Inter", 11, "bold"))
        except Exception:
            pass

    def _create_header(self):
        header = tk.Canvas(self, height=72, highlightthickness=0)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        # gradient-ish effect
        w = 1200
        for i, color in enumerate(["#5b8c85", "#6aa79f", "#84c1c6"]):
            header.create_rectangle(i * w // 3, 0, (i + 1) * w // 3, 72, fill=color, outline="")
        header.create_text(20, 36, anchor="w", text="Institute Management System", font=("Inter", 18, "bold"), fill="white")

        # small subtitle
        header.create_text(22, 52, anchor="w", text="Minimal • Clean • Usable", font=("Inter", 9), fill="white")

    def _create_sidebar(self):
        sidebar = ttk.Frame(self, width=220)
        sidebar.grid(row=1, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        buttons = [
            ("Dashboard", "DashboardPage"),
            ("Students", "StudentsPage"),
            ("Teachers", "TeachersPage"),
            ("Courses", "CoursesPage"),
            ("Reports", "ReportsPage"),
        ]
        for i, (text, page) in enumerate(buttons):
            b = ttk.Button(sidebar, text=text, command=lambda p=page: self.show_frame(p))
            b.pack(fill="x", padx=12, pady=(12 if i == 0 else 6))

        # footer small
        ttk.Label(sidebar, text="Corvit - IMS", font=("Inter", 9)).pack(side="bottom", pady=12)

    def _create_main_container(self):
        self.main_container = ttk.Frame(self)
        self.main_container.grid(row=1, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

    def show_frame(self, name):
        frame = self.frames[name]
        frame.refresh()
        frame.tkraise()


# ---------- Base Page ----------
class BasePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=12)
        self.controller = controller

    def refresh(self):
        """Override in pages to refresh content when shown."""
        pass


# ---------- Dashboard ----------
class DashboardPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Dashboard", style="Header.TLabel").pack(anchor="w")
        self.stats_frame = ttk.Frame(self, padding=(8, 12))
        self.stats_frame.pack(fill="both", expand=True)

        self.summary_text = tk.Text(self.stats_frame, height=10, wrap="word")
        self.summary_text.pack(fill="both", expand=True)

    def refresh(self):
        people = get_people()
        courses = get_courses()
        students = len([p for p in people if p[1] == "student"]) if people else 0
        teachers = len([p for p in people if p[1] == "teacher"]) if people else 0
        courses_count = len(courses)
        text = f"Total Students: {students}\nTotal Teachers: {teachers}\nTotal Courses: {courses_count}\n\n"
        text += "Quick lists:\n"
        cs = get_courses()
        for c in cs[:10]:
            text += f" - {c[2]} ({c[1]})\n"
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, text)


# ---------- Students Page ----------
class StudentsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        header = ttk.Label(self, text="Students", style="Header.TLabel")
        header.pack(anchor="w")

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, pady=(8, 0))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)

        # left: form
        form = ttk.LabelFrame(content, text="Student Form", padding=12)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w")
        self.s_name = ttk.Entry(form)
        self.s_name.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Email").grid(row=1, column=0, sticky="w")
        self.s_email = ttk.Entry(form)
        self.s_email.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Phone").grid(row=2, column=0, sticky="w")
        self.s_phone = ttk.Entry(form)
        self.s_phone.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Notes").grid(row=3, column=0, sticky="w")
        self.s_extra = ttk.Entry(form)
        self.s_extra.grid(row=3, column=1, sticky="ew", pady=4)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(8, 0))
        self.add_btn = ttk.Button(btn_frame, text="Add Student", command=self.add_student)
        self.add_btn.pack(side="left", padx=6)
        self.update_btn = ttk.Button(btn_frame, text="Update Selected", command=self.update_student)
        self.update_btn.pack(side="left", padx=6)
        self.del_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_student)
        self.del_btn.pack(side="left", padx=6)
        self.enroll_btn = ttk.Button(btn_frame, text="Enroll Selected", command=self.enroll_selected)
        self.enroll_btn.pack(side="left", padx=6)

        form.columnconfigure(1, weight=1)

        # right: treeview list
        list_frame = ttk.LabelFrame(content, text="Students List", padding=8)
        list_frame.grid(row=0, column=1, sticky="nsew", pady=4)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(list_frame, columns=("id", "name", "email", "phone"), show="headings", selectmode="browse")
        for col, txt in (("id", "ID"), ("name", "Name"), ("email", "Email"), ("phone", "Phone")):
            self.tree.heading(col, text=txt)
            self.tree.column(col, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.on_select_load)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

    def refresh(self):
        # load students
        for r in self.tree.get_children():
            self.tree.delete(r)
        students = get_people("student")
        if students:
            for s in students:
                self.tree.insert("", "end", values=(s[0], s[1], s[2] or "", s[3] or ""))

        # clear form
        self.clear_form()

    def clear_form(self):
        self.s_name.delete(0, tk.END)
        self.s_email.delete(0, tk.END)
        self.s_phone.delete(0, tk.END)
        self.s_extra.delete(0, tk.END)
        self._editing_id = None

    def add_student(self):
        name = self.s_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required.")
            return
        add_person("student", name, self.s_email.get().strip(), self.s_phone.get().strip(), self.s_extra.get().strip())
        messagebox.showinfo("Success", "Student added.")
        self.refresh()

    def on_select_load(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        pid = vals[0]
        # fetch full details
        rows = query("SELECT id,name,email,phone,extra FROM person WHERE id=?", (pid,), fetch=True)
        if rows:
            r = rows[0]
            self._editing_id = r[0]
            self.s_name.delete(0, tk.END); self.s_name.insert(0, r[1])
            self.s_email.delete(0, tk.END); self.s_email.insert(0, r[2] or "")
            self.s_phone.delete(0, tk.END); self.s_phone.insert(0, r[3] or "")
            self.s_extra.delete(0, tk.END); self.s_extra.insert(0, r[4] or "")

    def update_student(self):
        if not getattr(self, "_editing_id", None):
            messagebox.showwarning("No selection", "Double-click a row to load for editing.")
            return
        update_person(self._editing_id, self.s_name.get().strip(), self.s_email.get().strip(), self.s_phone.get().strip(), self.s_extra.get().strip())
        messagebox.showinfo("Updated", "Student updated.")
        self.refresh()

    def delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a student to delete.")
            return
        vals = self.tree.item(sel[0], "values")
        pid = vals[0]
        if messagebox.askyesno("Confirm", "Delete selected student? This will also remove enrollments."):
            delete_person(pid)
            self.refresh()

    def enroll_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a student to enroll.")
            return
        vals = self.tree.item(sel[0], "values")
        pid = vals[0]
        # choose course
        courses = get_courses()
        if not courses:
            messagebox.showwarning("No courses", "No courses exist. Add a course first.")
            return
        choices = [f"{c[0]}: {c[2]} ({c[1]})" for c in courses]
        choice = simpledialog.askstring("Enroll", "Type course id to enroll:\n" + "\n".join(choices))
        if not choice:
            return
        try:
            course_id = int(choice.split(":")[0].strip())
            ok = enroll_student(int(pid), course_id)
            if ok:
                messagebox.showinfo("Enrolled", "Student enrolled in course.")
            else:
                messagebox.showinfo("Already", "Student already enrolled in this course.")
        except Exception:
            messagebox.showerror("Error", "Invalid input.")
        self.refresh()


# ---------- Teachers Page ----------
class TeachersPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        header = ttk.Label(self, text="Teachers", style="Header.TLabel")
        header.pack(anchor="w")

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, pady=(8, 0))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)

        # left form
        form = ttk.LabelFrame(content, text="Teacher Form", padding=12)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w")
        self.t_name = ttk.Entry(form); self.t_name.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Email").grid(row=1, column=0, sticky="w")
        self.t_email = ttk.Entry(form); self.t_email.grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Phone").grid(row=2, column=0, sticky="w")
        self.t_phone = ttk.Entry(form); self.t_phone.grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Notes").grid(row=3, column=0, sticky="w")
        self.t_extra = ttk.Entry(form); self.t_extra.grid(row=3, column=1, sticky="ew", pady=4)

        btn_frame = ttk.Frame(form); btn_frame.grid(row=4, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(btn_frame, text="Add Teacher", command=self.add_teacher).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_teacher).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_teacher).pack(side="left", padx=6)

        form.columnconfigure(1, weight=1)

        # list
        list_frame = ttk.LabelFrame(content, text="Teachers List", padding=8)
        list_frame.grid(row=0, column=1, sticky="nsew", pady=4)
        list_frame.rowconfigure(0, weight=1); list_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(list_frame, columns=("id", "name", "email", "phone"), show="headings")
        for col, txt in (("id", "ID"), ("name", "Name"), ("email", "Email"), ("phone", "Phone")):
            self.tree.heading(col, text=txt)
            self.tree.column(col, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.on_select_load)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        teachers = get_people("teacher")
        if teachers:
            for s in teachers:
                self.tree.insert("", "end", values=(s[0], s[1], s[2] or "", s[3] or ""))
        self.clear_form()

    def clear_form(self):
        self.t_name.delete(0, tk.END); self.t_email.delete(0, tk.END)
        self.t_phone.delete(0, tk.END); self.t_extra.delete(0, tk.END)
        self._editing_id = None

    def add_teacher(self):
        name = self.t_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name required.")
            return
        add_person("teacher", name, self.t_email.get().strip(), self.t_phone.get().strip(), self.t_extra.get().strip())
        messagebox.showinfo("Success", "Teacher added.")
        self.refresh()

    def on_select_load(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        pid = vals[0]
        rows = query("SELECT id,name,email,phone,extra FROM person WHERE id=?", (pid,), fetch=True)
        if rows:
            r = rows[0]
            self._editing_id = r[0]
            self.t_name.delete(0, tk.END); self.t_name.insert(0, r[1])
            self.t_email.delete(0, tk.END); self.t_email.insert(0, r[2] or "")
            self.t_phone.delete(0, tk.END); self.t_phone.insert(0, r[3] or "")
            self.t_extra.delete(0, tk.END); self.t_extra.insert(0, r[4] or "")

    def update_teacher(self):
        if not getattr(self, "_editing_id", None):
            messagebox.showwarning("No selection", "Double-click a row to load for editing.")
            return
        update_person(self._editing_id, self.t_name.get().strip(), self.t_email.get().strip(), self.t_phone.get().strip(), self.t_extra.get().strip())
        messagebox.showinfo("Updated", "Teacher updated.")
        self.refresh()

    def delete_teacher(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a teacher to delete.")
            return
        vals = self.tree.item(sel[0], "values")
        pid = vals[0]
        if messagebox.askyesno("Confirm", "Delete selected teacher?"):
            delete_person(pid)
            self.refresh()


# ---------- Courses Page ----------
class CoursesPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        header = ttk.Label(self, text="Courses", style="Header.TLabel")
        header.pack(anchor="w")
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, pady=(8, 0))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)

        form = ttk.LabelFrame(content, text="Course Form", padding=10)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        ttk.Label(form, text="Code").grid(row=0, column=0, sticky="w")
        self.c_code = ttk.Entry(form); self.c_code.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Title").grid(row=1, column=0, sticky="w")
        self.c_title = ttk.Entry(form); self.c_title.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Duration").grid(row=2, column=0, sticky="w")
        self.c_duration = ttk.Entry(form); self.c_duration.grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Mode").grid(row=3, column=0, sticky="w")
        self.c_mode = ttk.Combobox(form, values=["Online", "Physical", "Hybrid"])
        self.c_mode.grid(row=3, column=1, sticky="ew", pady=4)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(btn_frame, text="Add Course", command=self.add_course).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_course).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_course).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Assign Teacher", command=self.assign_teacher).pack(side="left", padx=6)

        form.columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(content, text="Courses List", padding=8)
        list_frame.grid(row=0, column=1, sticky="nsew", pady=4)
        list_frame.rowconfigure(0, weight=1); list_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(list_frame, columns=("id", "code", "title", "duration", "mode"), show="headings")
        for col, txt in (("id", "ID"), ("code", "Code"), ("title", "Title"), ("duration", "Duration"), ("mode", "Mode")):
            self.tree.heading(col, text=txt)
            self.tree.column(col, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.load_course)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        courses = get_courses()
        if courses:
            for c in courses:
                self.tree.insert("", "end", values=(c[0], c[1], c[2], c[3] or "", c[4] or ""))
        self.clear_form()

    def clear_form(self):
        self.c_code.delete(0, tk.END); self.c_title.delete(0, tk.END)
        self.c_duration.delete(0, tk.END); self.c_mode.set("")
        self._editing_id = None

    def add_course(self):
        code = self.c_code.get().strip()
        title = self.c_title.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title required.")
            return
        try:
            add_course(code, title, self.c_duration.get().strip(), self.c_mode.get().strip())
            messagebox.showinfo("Added", "Course added.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Could not add course: {e}")

    def load_course(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        cid = vals[0]
        rows = query("SELECT id, code, title, duration, mode, teacher_id FROM course WHERE id=?", (cid,), fetch=True)
        if rows:
            r = rows[0]
            self._editing_id = r[0]
            self.c_code.delete(0, tk.END); self.c_code.insert(0, r[1] or "")
            self.c_title.delete(0, tk.END); self.c_title.insert(0, r[2] or "")
            self.c_duration.delete(0, tk.END); self.c_duration.insert(0, r[3] or "")
            self.c_mode.set(r[4] or "")

    def update_course(self):
        if not getattr(self, "_editing_id", None):
            messagebox.showwarning("No selection", "Double-click a course to load for editing.")
            return
        try:
            update_course(self._editing_id, self.c_code.get().strip(), self.c_title.get().strip(), self.c_duration.get().strip(), self.c_mode.get().strip(), None)
            messagebox.showinfo("Updated", "Course updated.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update: {e}")

    def delete_course(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a course to delete.")
            return
        vals = self.tree.item(sel[0], "values")
        cid = vals[0]
        if messagebox.askyesno("Confirm", "Delete this course?"):
            delete_course(cid)
            self.refresh()

    def assign_teacher(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a course first.")
            return
        vals = self.tree.item(sel[0], "values")
        cid = vals[0]
        teachers = get_people("teacher")
        if not teachers:
            messagebox.showwarning("No teachers", "Add a teacher first.")
            return
        choices = [f"{t[0]}: {t[1]}" for t in teachers]
        choice = simpledialog.askstring("Assign", "Type teacher id to assign:\n" + "\n".join(choices))
        if not choice:
            return
        try:
            tid = int(choice.split(":")[0].strip())
            assign_teacher_to_course(cid, tid)
            messagebox.showinfo("Assigned", "Teacher assigned to course.")
        except Exception:
            messagebox.showerror("Error", "Invalid input.")
        self.refresh()


# ---------- Reports Page ----------
class ReportsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        header = ttk.Label(self, text="Reports", style="Header.TLabel")
        header.pack(anchor="w")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, pady=(8, 0))

        self.tab_students = ttk.Frame(tabs); self.tab_teachers = ttk.Frame(tabs); self.tab_courses = ttk.Frame(tabs)
        tabs.add(self.tab_students, text="Students & Enrollments")
        tabs.add(self.tab_teachers, text="Teachers & Courses")
        tabs.add(self.tab_courses, text="Courses & Students")

        # students tab
        self.s_tree = ttk.Treeview(self.tab_students, columns=("student", "course"), show="headings")
        self.s_tree.heading("student", text="Student")
        self.s_tree.heading("course", text="Course")
        self.s_tree.pack(fill="both", expand=True, padx=8, pady=8)

        # teachers tab
        self.t_tree = ttk.Treeview(self.tab_teachers, columns=("teacher", "course"), show="headings")
        self.t_tree.heading("teacher", text="Teacher")
        self.t_tree.heading("course", text="Course")
        self.t_tree.pack(fill="both", expand=True, padx=8, pady=8)

        # courses tab
        self.c_tree = ttk.Treeview(self.tab_courses, columns=("course", "student"), show="headings")
        self.c_tree.heading("course", text="Course")
        self.c_tree.heading("student", text="Student")
        self.c_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self):
        # students & enrollments
        for t in (self.s_tree, self.t_tree, self.c_tree):
            for r in t.get_children(): t.delete(r)

        rows = query("""SELECT p.name, c.title FROM enrollment e
                        JOIN person p ON e.student_id = p.id
                        JOIN course c ON e.course_id = c.id
                        ORDER BY p.name""", fetch=True)
        if rows:
            for r in rows:
                self.s_tree.insert("", "end", values=(r[0], r[1]))

        trows = get_teachers_with_courses()
        if trows:
            for r in trows:
                # r: teacher_id, teacher_name, course_id, code, title
                teacher_name = r[1]
                course_title = r[4] or "—"
                self.t_tree.insert("", "end", values=(teacher_name, course_title))

        crows = get_courses_with_students()
        if crows:
            for r in crows:
                # r: course.id, code, title, student.id, student.name
                title = r[2] or "—"
                student_name = r[4] or "—"
                self.c_tree.insert("", "end", values=(title, student_name))


# ---------- Initialize and run ----------
if __name__ == "__main__":
    init_db()
    app = IMSApp()
    app.mainloop()
