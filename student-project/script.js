const API_BASE_CANDIDATES = [
  "http://127.0.0.1:5000",
  "http://127.0.0.1:5001",
  "http://localhost:5000",
  "http://localhost:5001"
];

let resolvedApiBaseUrl = null;
const CONNECT_RETRY_MS = 1000;
const CONNECT_TIMEOUT_MS = 30000;

const studentForm = document.getElementById("student-form");
const studentsTableBody = document.getElementById("students-table-body");
const statusMessage = document.getElementById("status-message");
const refreshButton = document.getElementById("refresh-btn");

function showStatus(message, type = "") {
  statusMessage.textContent = message;
  statusMessage.className = `status ${type}`.trim();
}

function clearForm() {
  studentForm.reset();
}

async function resolveApiBaseUrl() {
  if (resolvedApiBaseUrl) {
    return resolvedApiBaseUrl;
  }

  const deadline = Date.now() + CONNECT_TIMEOUT_MS;

  while (Date.now() < deadline) {
    for (const baseUrl of API_BASE_CANDIDATES) {
      try {
        const response = await fetch(`${baseUrl}/students`, { cache: "no-store" });
        const contentType = response.headers.get("content-type") || "";

        if (!response.ok || !contentType.includes("application/json")) {
          continue;
        }

        await response.clone().json();
        resolvedApiBaseUrl = baseUrl;
        showStatus(`Connected to backend at ${baseUrl}`, "success");
        return resolvedApiBaseUrl;
      } catch (error) {
        continue;
      }
    }

    showStatus("Starting Flask backend... waiting for connection.", "");
    await new Promise((resolve) => setTimeout(resolve, CONNECT_RETRY_MS));
  }

  throw new Error(
    "Could not connect to Flask backend after waiting. Start app.py and refresh the page."
  );
}

function renderStudents(students) {
  if (!students.length) {
    studentsTableBody.innerHTML = `
      <tr>
        <td colspan="8" class="empty">No students found.</td>
      </tr>
    `;
    return;
  }

  studentsTableBody.innerHTML = students.map((student) => `
    <tr>
      <td>${student.Student_ID ?? ""}</td>
      <td>${student.Name ?? ""}</td>
      <td>${student.DOB ?? ""}</td>
      <td>${student.Gender ?? ""}</td>
      <td>${student.Phone ?? ""}</td>
      <td>${student.Email ?? ""}</td>
      <td>${student.Dept_ID ?? ""}</td>
      <td>
        <button class="danger" data-id="${student.Student_ID}">Delete</button>
      </td>
    </tr>
  `).join("");
}

async function loadStudents() {
  try {
    const apiBaseUrl = await resolveApiBaseUrl();
    const response = await fetch(`${apiBaseUrl}/students`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Could not load students");
    }

    renderStudents(data);
    showStatus("Students loaded successfully.", "success");
  } catch (error) {
    studentsTableBody.innerHTML = `
      <tr>
        <td colspan="8" class="empty">Unable to load students.</td>
      </tr>
    `;
    showStatus(error.message, "error");
  }
}

async function addStudent(event) {
  event.preventDefault();

  const payload = {
    Name: document.getElementById("name").value.trim(),
    DOB: document.getElementById("dob").value,
    Gender: document.getElementById("gender").value,
    Phone: document.getElementById("phone").value.trim(),
    Email: document.getElementById("email").value.trim(),
    Dept_ID: document.getElementById("deptId").value ? Number(document.getElementById("deptId").value) : null
  };

  try {
    const apiBaseUrl = await resolveApiBaseUrl();
    const response = await fetch(`${apiBaseUrl}/students`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Could not add student");
    }

    showStatus(data.message || "Student added successfully.", "success");
    clearForm();
    await loadStudents();
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function deleteStudent(studentId) {
  const shouldDelete = window.confirm("Delete this student?");
  if (!shouldDelete) {
    return;
  }

  try {
    const apiBaseUrl = await resolveApiBaseUrl();
    const response = await fetch(`${apiBaseUrl}/students/${studentId}`, {
      method: "DELETE"
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Could not delete student");
    }

    showStatus(data.message || "Student deleted successfully.", "success");
    await loadStudents();
  } catch (error) {
    showStatus(error.message, "error");
  }
}

studentForm.addEventListener("submit", addStudent);

refreshButton.addEventListener("click", loadStudents);

studentsTableBody.addEventListener("click", (event) => {
  if (event.target.tagName === "BUTTON" && event.target.dataset.id) {
    deleteStudent(event.target.dataset.id);
  }
});

loadStudents();
