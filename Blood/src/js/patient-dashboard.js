const API_URL = "http://127.0.0.1:5000/api";

const token = localStorage.getItem("token");

if (!token) {
  window.location.href = "login.html";
}

const patientName = document.getElementById("patientName");
const totalRequests = document.getElementById("totalRequests");
const pendingRequests = document.getElementById("pendingRequests");
const completedRequests = document.getElementById("completedRequests");
const acceptedRequests = document.getElementById("acceptedRequests");

const rejectedRequests = document.getElementById("rejectedRequests");

const matchedRequests = document.getElementById("matchedRequests");

const cancelledRequests = document.getElementById("cancelledRequests");
const recentActivity = document.getElementById("recentActivity");
const requestContainer = document.getElementById("requestContainer");
const logoutBtn = document.getElementById("logoutBtn");

async function loadDashboard() {
  try {
    const response = await fetch(`${API_URL}/patients/dashboard`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.status === 401) {
      localStorage.clear();
      window.location.href = "login.html";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      alert(data.message);

      return;
    }

    patientName.innerHTML = `Welcome ${data.patient.full_name || ""}`;

   totalRequests.innerHTML = data.statistics.total_requests;

   pendingRequests.innerHTML = data.statistics.pending;

   completedRequests.innerHTML = data.statistics.completed;

   acceptedRequests.innerHTML = data.statistics.accepted;

   rejectedRequests.innerHTML = data.statistics.rejected;

   matchedRequests.innerHTML = data.statistics.matched;

   cancelledRequests.innerHTML = data.statistics.cancelled;
recentActivity.innerHTML = "";
    if (data.recent_activities.length === 0) {
      recentActivity.innerHTML = "<p>No recent activity.</p>";
    } else {
      data.recent_activities.forEach((activity) => {
      recentActivity.innerHTML += `
<div class="activity-card">
    <h4>🩸 Request #${activity.request_id}</h4>

    <p><strong>${activity.activity}</strong></p>

    <p>Blood Group : ${activity.blood_group}</p>

    <p>Hospital : ${activity.hospital}</p>

    <p>
        Status :
        <strong style="
            color:${
              activity.status === "Accepted"
                ? "green"
                : activity.status === "Pending"
                  ? "orange"
                  : activity.status === "Rejected"
                    ? "red"
                    : activity.status === "Completed"
                      ? "blue"
                      : "gray"
            };
        ">
            ${activity.status}
        </strong>
    </p>

    <small>${activity.request_time}</small>

    <hr>
</div>
`;
      });
    }
  } catch (error) {
    console.log(error);

    recentActivity.innerHTML = "<p>Unable to connect backend.</p>";
  }
}
async function loadRequests() {
  try {
    const response = await fetch(`${API_URL}/patients/requests`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.status === 401) {
      localStorage.clear();
      window.location.href = "login.html";
      return;
    }

    const requests = await response.json();

    if (!response.ok) {
      requestContainer.innerHTML = `<p>${requests.message}</p>`;

      return;
    }

    if (requests.length === 0) {
      requestContainer.innerHTML = "<p>No blood requests found.</p>";

      return;
    }

    requestContainer.innerHTML = "";

    requests.forEach((request) => {
      let donorHTML = "";

      if (request.matched_donors.length === 0) {
        donorHTML = `
                <p>
                    No matched donors yet.
                </p>
                `;
      } else {
        request.matched_donors.forEach((donor) => {
          donorHTML += `

                  
<div class="donor-card"
style="
border:2px solid ${donor.donor_response === "Accepted" ? "green" : "#ddd"};
background:${donor.donor_response === "Accepted" ? "#e8ffe8" : "#fff"};
">
                       <h4>
${donor.name}

${donor.donor_response === "Accepted" ? "✅ Accepted Donor" : ""}
</h4>
                        <p>

                            📞 ${donor.phone}

                        </p>

                        <p>

                            📧 ${donor.email}

                        </p>

                        <p>

                            Blood :
                            ${donor.blood_group}

                        </p>

                        <p>

                            Distance :
                            ${donor.distance_km} km

                        </p>

                        <p>

                            Ranking :
                            ${donor.ranking_score}

                        </p>

                        <p>

                            Reliability :
                            ${donor.reliability_score}

                        </p>

<p>
    Response :
    <strong style="
        color:${
          donor.donor_response === "Accepted"
            ? "green"
            : donor.donor_response === "Pending"
              ? "orange"
              : donor.donor_response === "Rejected"
                ? "red"
                : "gray"
        };
    ">
        ${donor.donor_response}
    </strong>
</p>
                        
                    </div>

                    `;
        });
      }

      requestContainer.innerHTML += `

            <div class="request-card">

                <h3>

                    Blood Request #${request.request_id}

                </h3>

                <p>

                    Blood Group :

                    ${request.blood_group}

                </p>

                <p>

                    Hospital :

                    ${request.hospital_name}

                </p>

                <p>

                    Emergency :

                    ${request.emergency_level}

                </p>

                <p>
Status :
<strong style="
color:
${
  request.status === "Accepted"
    ? "green"
    : request.status === "Pending"
      ? "orange"
      : request.status === "Rejected"
        ? "red"
        : request.status === "Completed"
          ? "blue"
          : "gray"
};
">
${request.status}
</strong>
</p>

                <p>

                    Units :

                    ${request.units_needed}

                </p>

                <hr>

                <h4>
    Matched Donors (${request.matched_donors.length})
</h4>

                ${donorHTML}

            </div>

            `;
    });
  } catch (error) {
    console.log(error);

    requestContainer.innerHTML = "<p>Unable to load requests.</p>";
  }
}
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("token");

  localStorage.removeItem("user");

  window.location.href = "login.html";
});
loadDashboard();

loadRequests();
setInterval(() => {
  loadDashboard();

  loadRequests();
}, 5000)