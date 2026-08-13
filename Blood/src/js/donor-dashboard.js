const API_URL = "http://127.0.0.1:5000";

const token = localStorage.getItem("token");

const donorInfo = document.getElementById("donorInfo");
const performanceStats = document.getElementById("performanceStats");
const availabilityControl = document.getElementById("availabilityControl");
const rewardStats = document.getElementById("rewardStats");
const requestsContainer = document.getElementById("requestsContainer");
const logoutButton = document.getElementById("logoutButton");
const badgeCard = document.getElementById("badgeCard");

const pointsCard = document.getElementById("pointsCard");

const eligibleCard = document.getElementById("eligibleCard");

const recentDonations = document.getElementById("recentDonations");
let activeTimers = {};
let isRefreshingRequests = false;

// =====================================================
// AUTHENTICATION CHECK
// =====================================================

if (!token) {
  window.location.href = "login.html";
}

// =====================================================
// LOAD DONOR DASHBOARD
// =====================================================

async function loadDonorDashboard() {
  const token = localStorage.getItem("token");

  console.log("TOKEN:", token);
  try {
    const response = await fetch(`${API_URL}/api/donors/dashboard`, {
      method: "GET",

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
      donorInfo.innerHTML = `
        <div class="request-info">
          <p>Unable to load donor dashboard.</p>
        </div>
      `;

      return;
    }

    const donor = data.donor || data;

    // =====================================================
    // DONOR PROFILE
    // =====================================================

    donorInfo.innerHTML = `

<div class="request-info">

<p><strong>Name:</strong> ${donor.full_name || "N/A"}</p>

<p><strong>Phone:</strong> ${donor.phone || "N/A"}</p>

<p><strong>Email:</strong> ${donor.email || "N/A"}</p>

<p><strong>Blood Group:</strong> ${donor.blood_group}</p>

<p><strong>Age:</strong> ${donor.age}</p>

<p><strong>Gender:</strong> ${donor.gender}</p>

<p><strong>Address:</strong> ${donor.address || "N/A"}</p>

<p><strong>Availability:</strong>
<span style="
color:${donor.availability ? "green" : "red"};
font-weight:bold;
">
${donor.availability ? "Available" : "Unavailable"}
</span>
</p>

<p><strong>Total Donations:</strong>
${donor.total_donations}
</p>

<p><strong>Reliability Score:</strong>
${donor.reliability_score}
</p>

<p><strong>Reward Points:</strong>
${donor.reward_points}
</p>

<p><strong>Badge:</strong>
🏅 ${donor.badge}
</p>

<p><strong>Achievements:</strong>
${donor.badges ? donor.badges.join(", ") : "None"}
</p>

<p><strong>Last Donation:</strong>
${donor.last_donation_date || "N/A"}
</p>

<p><strong>Next Eligible Date:</strong>
${donor.next_eligible_date || "Eligible"}
</p>
</div>

`;

    // =====================================================
    // AVAILABILITY CONTROL
    // =====================================================

    availabilityControl.innerHTML = `

            <h3>
                Update Availability
            </h3>

            <select id="availabilitySelect">

                <option
                    value="true"
                    ${data.availability === true ? "selected" : ""}
                >
                    Available
                </option>

                <option
                    value="false"
                    ${data.availability === false ? "selected" : ""}
                >
                    Unavailable
                </option>

            </select>

            <button
                onclick="updateAvailability()"
            >
                Update Availability
            </button>

        `;

    // =====================================================
    // PERFORMANCE STATISTICS
    // =====================================================

    performanceStats.innerHTML = `

            <h3>
                Donor Performance
            </h3>

            <div class="request-info">

                <p>
                    <strong>Total Requests:</strong>
                    ${data.total_requests || 0}
                </p>

                <p>
                    <strong>Accepted Requests:</strong>
                    ${data.accepted_requests || 0}
                </p>

                <p>
                    <strong>Rejected Requests:</strong>
                    ${data.rejected_requests || 0}
                </p>

                <p>
                    <strong>Acceptance Rate:</strong>
                    ${data.acceptance_rate || 0}%
                </p>

            </div>

        `;

    // =====================================================
    // REWARD STATISTICS
    // =====================================================

    rewardStats.innerHTML = `
<h3>Rewards & Achievements</h3>

<div class="request-info">

<p><strong>Reward Points:</strong>
${donor.reward_points}
</p>

<p><strong>Main Badge:</strong>
🏅 ${donor.badge}
</p>

<p><strong>Achievements:</strong>
${donor.badges ? donor.badges.join(", ") : "None"}
</p>

</div>
`;
    // =========================
    // SUMMARY CARDS
    // =========================

    badgeCard.innerHTML = "🏅 " + donor.badge;

    pointsCard.innerHTML = donor.reward_points;

    eligibleCard.innerHTML = donor.next_eligible_date || "Eligible Now";

    if (!data.recent_donations || data.recent_donations.length === 0) {
      recentDonations.innerHTML = "<p>No recent donations.</p>";
    } else {
      recentDonations.innerHTML = "";

      data.recent_donations.forEach((donation) => {
        recentDonations.innerHTML += `

            <div class="request-info">

                <p><strong>Date:</strong> ${donation.donation_date}</p>

                <p><strong>Units:</strong> ${donation.units_donated}</p>

                <p><strong>Status:</strong> ${donation.donation_status}</p>

            </div>

            `;
      });
    }
  } catch (error) {
    console.error("Dashboard Error:", error);

    donorInfo.innerHTML = `
            <p>
                Unable to connect to backend.
            </p>
        `;

    performanceStats.innerHTML = `
            <p>
                Unable to load performance statistics.
            </p>
        `;

    availabilityControl.innerHTML = "";

    rewardStats.innerHTML = "";
  }
}

// =====================================================
// LOAD INCOMING BLOOD REQUESTS
// =====================================================

async function loadIncomingRequests() {
  if (isRefreshingRequests) {
    return;
  }

  isRefreshingRequests = true;

  try {
    const response = await fetch(
      `${API_URL}/api/donors/requests`,

      {
        method: "GET",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

  if (response.status === 401) {
    localStorage.clear();
    window.location.href = "login.html";
    return;
  }

  const data = await response.json();
  const requests = data.requests || data;
    if (!response.ok) {
      requestsContainer.innerHTML = `

                <p class="empty">

                    ${data.message || "Failed to load requests"}

                </p>

            `;

      return;
    }

    // =====================================================
    // STOP OLD TIMERS
    // =====================================================

    Object.values(activeTimers).forEach((timer) => clearInterval(timer));

    activeTimers = {};

    // =====================================================
    // FILTER ACTIVE REQUESTS
    // =====================================================
    const activeRequests = requests.filter(
      (request) => request.donor_response === "Pending",
    );

    console.log("All Requests:", requests);

    requests.forEach((r) => {
      console.log(r.match_id, r.request_id, r.donor_response, r.request_status);
    });

    if (activeRequests.length === 0) {
      requestsContainer.innerHTML = `

                <p class="empty">

                    No incoming blood requests.

                </p>

            `;

      return;
    }

    requestsContainer.innerHTML = "";

    // =====================================================
    // CREATE REQUEST CARDS
    // =====================================================

    activeRequests.forEach((request) => {
      const card = document.createElement("div");

      card.className = "request-card";

      card.innerHTML = `

                    <h3>

                        Blood Request
                        #${request.request_id}

                    </h3>


                    <div class="request-info">


                        <p>

                            <strong>
                               🩸 Blood Group :
                            </strong>

                            ${request.blood_group || "N/A"}

                        </p>


                        <p>

                            <strong>
                                Units Needed:
                            </strong>

                            ${request.units_needed || "N/A"}

                        </p>


                        <p>

                            <strong>
                               🚨 Emergency :
                            </strong>

                           <span style="
color:
${
  request.emergency_level === "CRITICAL"
    ? "red"
    : request.emergency_level === "HIGH"
      ? "orange"
      : request.emergency_level === "MEDIUM"
        ? "blue"
        : "green"
};
font-weight:bold;
">

${request.emergency_level}

</span>

                        </p>

<p>

<strong>Patient Name:</strong>

${request.patient_name || "N/A"}

</p>
<p>

<strong>Patient Phone:</strong>

${request.patient_phone || "N/A"}

</p>
                        <p>

                            <strong>
                               🏥 Hospital :
                            </strong>

                            ${request.hospital_name || "N/A"}

                        </p>

<p>

<button
onclick="openMap(
${request.hospital_latitude},
${request.hospital_longitude}
)">
📍 View Hospital Location
</button>

</p>
<div
id="map-${request.match_id}"
style="
height:220px;
margin-top:10px;
border-radius:10px;
">
</div>
                       <p>

<strong>Distance:</strong>

<span style="color:green;font-weight:bold;">

${request.distance_km != null ? Number(request.distance_km).toFixed(1) : "N/A"}

km

</span>

</p>


                        <p>

                            <strong>
                                Ranking Score:
                            </strong>

                            ${request.ranking_score || 0}

                        </p>


                        <p>

                            <strong>
                                Response Probability:
                            </strong>

                            ${request.response_probability || 0}%

                        </p>


                        <p>

                            <strong>
                                Status:
                            </strong>

                            ${request.donor_response || "Pending"}

                        </p>


                    </div>


                    ${
                      request.donor_response === "Pending" &&
                      request.response_deadline
                        ? `

                                <div

                                    id="timer-${request.match_id}"

                                    class="response-timer"

                                >

                                    Loading timer...

                                </div>

                            `
                        : ""
                    }


                    ${
                      request.donor_response === "Pending"
                        ? `

                                <div
                                    class="response-buttons"
                                >


                                    <button

                                        class="accept-button"

                                        onclick="respondToRequest(

                                            ${request.match_id},

                                            'Accepted'

                                        )"

                                    >

                                        Accept

                                    </button>


                                    <button

                                        class="reject-button"

                                        onclick="respondToRequest(

                                            ${request.match_id},

                                            'Rejected'

                                        )"

                                    >

                                        Reject

                                    </button>


                                </div>

                            `
                        : ""
                    }

                `;

      requestsContainer.appendChild(card);
      const map = L.map(`map-${request.match_id}`).setView(
        [request.hospital_latitude, request.hospital_longitude],
        13,
      );

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
      }).addTo(map);

      L.marker([request.hospital_latitude, request.hospital_longitude])
        .addTo(map)
        .bindPopup(request.hospital_name)
        .openPopup();

      // =====================================================
      // START COUNTDOWN TIMER
      // =====================================================

      if (request.donor_response === "Pending" && request.response_deadline) {
        const timerElement = document.getElementById(
          `timer-${request.match_id}`,
        );

        if (timerElement) {
          startCountdown(
            timerElement,

            request.response_deadline,

            request.match_id,
          );
        }
      }
    });
  } catch (error) {
    console.error(
      "Requests Error:",

      error,
    );

    requestsContainer.innerHTML = `

            <p class="empty">

                Unable to connect to backend.

            </p>

        `;
  } finally {
    isRefreshingRequests = false;
  }
}

// =====================================================
// COUNTDOWN TIMER
// =====================================================

function startCountdown(
  element,

  deadline,

  matchId,
) {
  const deadlineTime = new Date(deadline).getTime();

  function updateTimer() {
    const now = new Date().getTime();

    const remaining = deadlineTime - now;

    if (remaining <= 0) {
      element.innerHTML = `

                ⏰

                <strong>

                    Response time expired.

                </strong>

            `;

      element.classList.add("expired");

      clearInterval(activeTimers[matchId]);

      delete activeTimers[matchId];

      // Refresh requests.
      // Backend scheduler will process timeout.

      setTimeout(
        () => {
          loadIncomingRequests();
        },

        2000,
      );

      return;
    }

    const minutes = Math.floor(remaining / (1000 * 60));

    const seconds = Math.floor((remaining % (1000 * 60)) / 1000);

    element.innerHTML = `

            ⏱️

            Respond within:

            <strong>

                ${String(minutes).padStart(
                  2,

                  "0",
                )}:${String(seconds).padStart(
                  2,

                  "0",
                )}

            </strong>

        `;
  }

  updateTimer();

  activeTimers[matchId] = setInterval(
    updateTimer,

    1000,
  );
}

// =====================================================
// UPDATE DONOR AVAILABILITY
// =====================================================

async function updateAvailability() {
  const select = document.getElementById("availabilitySelect");

  if (!select) {
    return;
  }

  const availability = select.value === "true";

  try {
    const response = await fetch(`${API_URL}/api/donors/availability`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ availability: availability }),
    });

    if (response.status === 401) {
      localStorage.clear();
      window.location.href = "login.html";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      alert(data.message || "Failed to update availability");

      return;
    }

    alert("Availability updated successfully");

    await loadDonorDashboard();

    await loadIncomingRequests();
  } catch (error) {
    console.error(
      "Availability Error:",

      error,
    );

    alert("Unable to connect to backend");
  }
}

// =====================================================
// ACCEPT / REJECT REQUEST
// =====================================================

async function respondToRequest(matchId, response) {
  document
    .querySelectorAll(".accept-button,.reject-button")
    .forEach((btn) => (btn.disabled = true));
  try {
    const result = await fetch(`${API_URL}/api/donors/requests/${matchId}/respond`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ response: response }),
    });

    if (result.status === 401) {
      localStorage.clear();
      window.location.href = "login.html";
      return;
    }

    const data = await result.json();

    if (!result.ok) {
      alert(data.message || "Failed to respond to request");
      return;
    }

    alert(data.message);

    await loadIncomingRequests();
    await loadDonorDashboard();
  } catch (error) {
    console.error(error);

    alert("Unable to connect backend");
  }
}

// =====================================================
// LOGOUT
// =====================================================

if (logoutButton) {
  logoutButton.addEventListener(
    "click",

    function () {
      localStorage.removeItem("token");

      localStorage.removeItem("user");

      localStorage.removeItem("patient_id");

      window.location.href = "login.html";
    },
  );
}

// =====================================================
// INITIAL LOAD
// =====================================================
loadDonorDashboard();
loadIncomingRequests();

function openMap(lat, lng) {
  window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
}