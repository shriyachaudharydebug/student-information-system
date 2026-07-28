# ============================================================
#  Student Information System — Flask Backend
#  Database : MySQL  →  student_info_system
#  Driver   : mysql-connector-python  (NO SQLAlchemy)
#  Auth     : hardcoded users  (no JWT, no hashing)
#
#  NOTE: Your tables use plain INT PRIMARY KEY (no AUTO_INCREMENT).
#        For every INSERT we auto-calculate the next available ID
#        using MAX(pk_column) + 1 so you never get a duplicate.
# ============================================================

from pathlib import Path
import socket

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)   # lets the HTML frontend call this API from the browser
BASE_DIR = Path(__file__).resolve().parent

# ------------------------------------------------------------
# DATABASE CONFIG  ← put your MySQL password here
# ------------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "jay@2017",   # <-- change this
    "database": "student_info_system"
}

def get_db():
    """Open and return a fresh MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)

def next_id(cursor, table, pk_col):
    """
    Return MAX(pk_col) + 1 for the given table.
    Returns 1 when the table is empty.
    Used because your tables have plain INT PK (no AUTO_INCREMENT).
    """
    cursor.execute(f"SELECT COALESCE(MAX({pk_col}), 0) + 1 AS nid FROM {table}")
    return cursor.fetchone()["nid"]


def choose_server_port():
    """
    Prefer port 5000, but fall back to 5001 when macOS AirPlay Receiver
    or another process is already bound to 5000.
    """
    for port in (5000, 5001):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError("Neither port 5000 nor 5001 is available.")


# ------------------------------------------------------------
# HARDCODED USERS  (no database, no JWT, no hashing)
# ------------------------------------------------------------
USERS = {
    "admin":   {"password": "admin123",   "role": "admin"},
    "student": {"password": "student123", "role": "student"},
    "faculty": {"password": "faculty123", "role": "faculty"},
}


# ============================================================
#  FRONTEND
# ============================================================

@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/script.js", methods=["GET"])
def serve_script():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/student_info_system_full.html", methods=["GET"])
def serve_full_dashboard():
    return send_from_directory(BASE_DIR, "student_info_system_full.html")


# ============================================================
#  AUTH
# ============================================================

# POST /login
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    user = USERS.get(username)
    if user and user["password"] == password:
        return jsonify({"success": True, "role": user["role"], "username": username})

    return jsonify({"success": False, "message": "Invalid username or password"}), 401


# ============================================================
#  DEPARTMENTS
# ============================================================

# GET /departments  — return all departments
@app.route("/departments", methods=["GET"])
def get_departments():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Department")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# POST /departments  — add a new department
@app.route("/departments", methods=["POST"])
def add_department():
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    new_id = next_id(cursor, "Department", "Dept_ID")

    cursor.execute(
        "INSERT INTO Department (Dept_ID, Dept_Name, HOD) VALUES (%s, %s, %s)",
        (new_id, data["Dept_Name"], data.get("HOD", ""))
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Department added", "Dept_ID": new_id}), 201

# PUT /departments/<id>  — update a department
@app.route("/departments/<int:dept_id>", methods=["PUT"])
def update_department(dept_id):
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Department SET Dept_Name=%s, HOD=%s WHERE Dept_ID=%s",
        (data["Dept_Name"], data.get("HOD", ""), dept_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Department updated"})

# DELETE /departments/<id>
@app.route("/departments/<int:dept_id>", methods=["DELETE"])
def delete_department(dept_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Department WHERE Dept_ID = %s", (dept_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Department deleted"})


# ============================================================
#  STUDENTS
# ============================================================

# GET /students  — return all students
@app.route("/students", methods=["GET"])
def get_students():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT Student_ID, Name,
                  DATE_FORMAT(DOB, '%Y-%m-%d') AS DOB,
                  Gender, Phone, Email, Dept_ID
           FROM Student
           ORDER BY Student_ID ASC"""
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# POST /students  — add a new student
@app.route("/students", methods=["POST"])
def add_student():
    data = request.json or {}
    name = data.get("Name", "").strip()

    if not name:
        return jsonify({"message": "Name is required"}), 400

    dept_id = data.get("Dept_ID")
    if dept_id in ("", None):
        dept_id = None

    dob = data.get("DOB")
    if dob == "":
        dob = None

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    new_id = next_id(cursor, "Student", "Student_ID")

    cursor.execute(
        """INSERT INTO Student (Student_ID, Name, DOB, Gender, Phone, Email, Dept_ID)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            new_id,
            name,
            dob,
            data.get("Gender"),
            data.get("Phone"),
            data.get("Email"),
            dept_id
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Student added", "Student_ID": new_id}), 201

# PUT /students/<id>  — update a student
@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.json or {}
    name = data.get("Name", "").strip()

    if not name:
        return jsonify({"message": "Name is required"}), 400

    dept_id = data.get("Dept_ID")
    if dept_id in ("", None):
        dept_id = None

    dob = data.get("DOB")
    if dob == "":
        dob = None

    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE Student
           SET Name=%s, DOB=%s, Gender=%s, Phone=%s, Email=%s, Dept_ID=%s
           WHERE Student_ID=%s""",
        (
            name,
            dob,
            data.get("Gender"),
            data.get("Phone"),
            data.get("Email"),
            dept_id,
            student_id
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Student updated"})

# DELETE /students/<id>  — cascades: removes grades & enrollments first
@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Grade      WHERE Student_ID = %s", (student_id,))
    cursor.execute("DELETE FROM Enrollment WHERE Student_ID = %s", (student_id,))
    cursor.execute("DELETE FROM Student    WHERE Student_ID = %s", (student_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()
    if deleted == 0:
        return jsonify({"message": "Student not found"}), 404
    return jsonify({"message": "Student deleted"})


# ============================================================
#  FACULTY
# ============================================================

# GET /faculty  — return all faculty
@app.route("/faculty", methods=["GET"])
def get_faculty():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Faculty")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# POST /faculty  — add a faculty member
@app.route("/faculty", methods=["POST"])
def add_faculty():
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    new_id = next_id(cursor, "Faculty", "Faculty_ID")

    cursor.execute(
        "INSERT INTO Faculty (Faculty_ID, Faculty_Name, Dept_ID, Email) VALUES (%s, %s, %s, %s)",
        (new_id, data["Faculty_Name"], data.get("Dept_ID"), data.get("Email"))
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Faculty added", "Faculty_ID": new_id}), 201

# PUT /faculty/<id>
@app.route("/faculty/<int:faculty_id>", methods=["PUT"])
def update_faculty(faculty_id):
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Faculty SET Faculty_Name=%s, Dept_ID=%s, Email=%s WHERE Faculty_ID=%s",
        (data["Faculty_Name"], data.get("Dept_ID"), data.get("Email"), faculty_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Faculty updated"})

# DELETE /faculty/<id>
@app.route("/faculty/<int:faculty_id>", methods=["DELETE"])
def delete_faculty(faculty_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Faculty WHERE Faculty_ID = %s", (faculty_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Faculty deleted"})


# ============================================================
#  COURSES
# ============================================================

# GET /courses  — return all courses
@app.route("/courses", methods=["GET"])
def get_courses():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Course")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# POST /courses  — add a course
@app.route("/courses", methods=["POST"])
def add_course():
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    new_id = next_id(cursor, "Course", "Course_ID")

    cursor.execute(
        "INSERT INTO Course (Course_ID, Course_Name, Credits, Dept_ID) VALUES (%s, %s, %s, %s)",
        (new_id, data["Course_Name"], data.get("Credits", 3), data.get("Dept_ID"))
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Course added", "Course_ID": new_id}), 201

# PUT /courses/<id>
@app.route("/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Course SET Course_Name=%s, Credits=%s, Dept_ID=%s WHERE Course_ID=%s",
        (data["Course_Name"], data.get("Credits", 3), data.get("Dept_ID"), course_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Course updated"})

# DELETE /courses/<id>
@app.route("/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Grade      WHERE Course_ID = %s", (course_id,))
    cursor.execute("DELETE FROM Enrollment WHERE Course_ID = %s", (course_id,))
    cursor.execute("DELETE FROM Course     WHERE Course_ID = %s", (course_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Course deleted"})


# ============================================================
#  ENROLLMENT
# ============================================================

# GET /enrollments  — return all enrollments
@app.route("/enrollments", methods=["GET"])
def get_enrollments():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Enrollment")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# POST /enroll  — enroll a student in a course
@app.route("/enroll", methods=["POST"])
def enroll_student():
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    new_id = next_id(cursor, "Enrollment", "Enrollment_ID")

    cursor.execute(
        """INSERT INTO Enrollment (Enrollment_ID, Student_ID, Course_ID, Semester, Year)
           VALUES (%s, %s, %s, %s, %s)""",
        (
            new_id,
            data["Student_ID"],
            data["Course_ID"],
            data.get("Semester", "Fall"),
            data.get("Year", 2024)
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Student enrolled", "Enrollment_ID": new_id}), 201

# GET /students/<id>/enrollments  — enrollments for one student
@app.route("/students/<int:student_id>/enrollments", methods=["GET"])
def get_student_enrollments(student_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM Enrollment WHERE Student_ID = %s", (student_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# DELETE /enrollments/<id>  — remove one enrollment row
@app.route("/enrollments/<int:enrollment_id>", methods=["DELETE"])
def delete_enrollment(enrollment_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Enrollment WHERE Enrollment_ID = %s", (enrollment_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Enrollment removed"})


# ============================================================
#  GRADES
# ============================================================

# GET /grades  — return all grades
@app.route("/grades", methods=["GET"])
def get_grades():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Grade")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# POST /grades  — assign a grade (updates if one already exists)
@app.route("/grades", methods=["POST"])
def add_grade():
    data   = request.get_json()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    # Check for an existing grade for this student + course pair
    cursor.execute(
        "SELECT Grade_ID FROM Grade WHERE Student_ID=%s AND Course_ID=%s",
        (data["Student_ID"], data["Course_ID"])
    )
    existing = cursor.fetchone()

    if existing:
        # Update the existing row — no new ID needed
        cursor.execute(
            "UPDATE Grade SET Grade=%s WHERE Grade_ID=%s",
            (data["Grade"], existing["Grade_ID"])
        )
        conn.commit()
        msg    = "Grade updated"
        grd_id = existing["Grade_ID"]
    else:
        # Insert a brand-new row with the next available ID
        new_id = next_id(cursor, "Grade", "Grade_ID")
        cursor.execute(
            "INSERT INTO Grade (Grade_ID, Student_ID, Course_ID, Grade) VALUES (%s, %s, %s, %s)",
            (new_id, data["Student_ID"], data["Course_ID"], data["Grade"])
        )
        conn.commit()
        msg    = "Grade added"
        grd_id = new_id

    cursor.close()
    conn.close()
    return jsonify({"message": msg, "Grade_ID": grd_id}), 201

# GET /students/<id>/grades  — all grades for one student
@app.route("/students/<int:student_id>/grades", methods=["GET"])
def get_student_grades(student_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM Grade WHERE Student_ID = %s", (student_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# DELETE /grades/<id>  — remove one grade row
@app.route("/grades/<int:grade_id>", methods=["DELETE"])
def delete_grade(grade_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Grade WHERE Grade_ID = %s", (grade_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Grade deleted"})


# ============================================================
#  RUN
# ============================================================
if __name__ == "__main__":
    server_port = choose_server_port()
    if server_port != 5000:
        print(
            f"Port 5000 is busy on this Mac, so Flask is starting on "
            f"http://127.0.0.1:{server_port}"
        )
    app.run(host="127.0.0.1", port=server_port, debug=False)
