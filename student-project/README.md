# Student Information System

A simple student management project with:

- A Flask backend using `mysql-connector-python`
- A plain HTML/CSS/JavaScript frontend
- MySQL database support
- Add, view, and delete student records
- A full dashboard page with login, plus a simpler student-only page

## Project Files

- `app.py` - Flask backend and API routes
- `index.html` - simple student CRUD page
- `script.js` - frontend fetch logic for the simple page
- `student_info_system_full.html` - full dashboard with login and all sections
- `requirements.txt` - Python dependencies
- `.vscode/tasks.json` - auto-start Flask when the folder opens in VS Code

## Features

- Add student
- View students
- Delete student
- Login page in the full dashboard
- Automatic backend port fallback if `5000` is busy

## Requirements

- Python 3
- MySQL Server
- MySQL Workbench is optional, but useful for checking data

## Install Dependencies

```bash
pip3 install -r requirements.txt
```

## Database Setup

The backend expects this MySQL database:

- Database name: `student_info_system`

The code also expects these tables to exist:

- `Student`
- `Department`
- `Faculty`
- `Course`
- `Enrollment`
- `Grade`

If your MySQL username or password is different, update `DB_CONFIG` in `app.py`.

## Run the Project

### Option 1: Flask-served pages

```bash
python3 app.py
```

Then open one of these in your browser:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/student_info_system_full.html`

If port `5000` is busy on your Mac, Flask automatically falls back to `5001`, and the frontend will try both ports.

### Option 2: VS Code auto-start

If you open the folder in VS Code, the backend task can start automatically from `.vscode/tasks.json`.

## Login Details

The full dashboard uses hardcoded logins:

- `admin / admin123`
- `student / student123`
- `faculty / faculty123`

## API Endpoints

- `POST /login`
- `GET /students`
- `POST /students`
- `DELETE /students/<id>`
- `GET /departments`
- `GET /faculty`
- `GET /courses`
- `GET /enrollments`
- `GET /grades`

## How The Frontend Connects

- The form in `index.html` collects student data.
- `script.js` sends JSON with `fetch()` to the Flask API.
- Flask reads the JSON with `request.json`.
- Flask writes the data into MySQL using `mysql-connector-python`.
- The table refreshes after add and delete actions.

## Check Data In MySQL Workbench

To confirm changes were saved, run:

```sql
USE student_info_system;
SELECT * FROM Student;
```

To check one record:

```sql
SELECT * FROM Student WHERE Student_ID = 104;
```

## Notes

- The simple page is best for student add/view/delete testing.
- The full dashboard includes the login page and more sections.
- If you see an old page in the browser, hard refresh with `Cmd + Shift + R`.
