const API_URL = "http://127.0.0.1:5000/api";

const token = localStorage.getItem("token");

async function loadPatientDashboard() {
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/patients/dashboard`, {
      method: "GET",

      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return;
    }

    // Save patient ID
    localStorage.setItem("patient_id", data.patient.patient_id);

    // Patient name
    document.getElementById("patientName").textContent =
      `Welcome, ${data.patient.name || "Patient"}`;

    // Dashboard counts
    document.getElementById("totalRequests").textContent = data.total_requests;

    document.getElementById("pendingRequests").textContent =
      data.pending_requests;

    document.getElementById("completedRequests").textContent =
      data.completed_requests;

    // Recent activity
    document.getElementById("recentActivity").innerHTML = `

            <p>
                You have created
                <strong>${data.total_requests}</strong>
                blood request(s).
            </p>

            <p>
                Pending requests:
                <strong>${data.pending_requests}</strong>
            </p>

            <p>
                Completed requests:
                <strong>${data.completed_requests}</strong>
            </p>

        `;
  } catch (error) {
    console.error("Dashboard Error:", error);
  }
}

// Logout
document.getElementById("logoutBtn")?.addEventListener("click", function () {
  localStorage.removeItem("token");

  localStorage.removeItem("user");

  localStorage.removeItem("patient_id");

  window.location.href = "login.html";
});

loadPatientDashboard();
