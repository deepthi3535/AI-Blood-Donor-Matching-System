const API_URL = "http://127.0.0.1:5000";

const token = localStorage.getItem("token");

// ==========================================
// Load Patient Dashboard
// ==========================================

async function loadPatientDashboard() {
  if (!token) {
    window.location.href = "login.html";

    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/api/patients/dashboard`,

      {
        method: "GET",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const data = await response.json();

    if (!response.ok) {
      console.error(data);

      return;
    }

    // ==========================================
    // Save Patient ID
    // ==========================================

    if (data.patient) {
      localStorage.setItem(
        "patient_id",

        data.patient.patient_id,
      );
    }

    // ==========================================
    // Patient Name
    // ==========================================

    const patientName = document.getElementById("patientName");

    if (patientName && data.patient) {
     patientName.textContent =
`Welcome ${data.patient.full_name}`;
    }

    // ==========================================
    // Dashboard Statistics
    // ==========================================
patientName.textContent = `Welcome ${data.patient.full_name}`;

document.getElementById("totalRequests").textContent =
  data.statistics.total_requests;

document.getElementById("pendingRequests").textContent =
  data.statistics.pending;

document.getElementById("matchedRequests").textContent =
  data.statistics.matched;

document.getElementById("acceptedRequests").textContent =
  data.statistics.accepted;

document.getElementById("completedRequests").textContent =
  data.statistics.completed;

document.getElementById("rejectedRequests").textContent =
  data.statistics.rejected;

document.getElementById("cancelledRequests").textContent =
  data.statistics.cancelled;
    // ==========================================
    // Recent Activity
    // ==========================================
const recentActivity = document.getElementById("recentActivity");

recentActivity.innerHTML = "";

if (data.recent_activities.length === 0) {

    recentActivity.innerHTML = "<p>No recent activity.</p>";

} else {

    data.recent_activities.forEach(activity => {

        recentActivity.innerHTML += `

<div class="activity-card">

<h3>Request #${activity.request_id}</h3>

<p>${activity.activity}</p>

<p>🩸 ${activity.blood_group}</p>

<p>🏥 ${activity.hospital}</p>

<p>Status :
<b>${activity.status}</b>
</p>

<p>🕒 ${activity.request_time}</p>

</div>

`;

    });

  }
} catch (error) {
    console.error(error);
  }
}
// ==========================================
// Logout
// ==========================================

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener(
    "click",

    function () {
      localStorage.removeItem("token");

      localStorage.removeItem("user");

      localStorage.removeItem("patient_id");

      window.location.href = "login.html";
    },
  );
}

// ==========================================
// Load Dashboard
// ==========================================

loadPatientDashboard();
