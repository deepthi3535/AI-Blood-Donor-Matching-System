const API_URL = "http://127.0.0.1:5000";

const token = localStorage.getItem("token");

const requestsContainer = document.getElementById("requestsContainer");

// =====================================================
// LOAD MY BLOOD REQUESTS
// =====================================================

async function loadMyRequests() {
  if (!token) {
    window.location.href = "login.html";

    return;
  }

  requestsContainer.innerHTML = `

    <p class="loading">

      Loading your blood requests...

    </p>

  `;

  try {
    const response = await fetch(
      `${API_URL}/api/requests/`,

      {
        method: "GET",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const data = await response.json();
    console.log(data);

    if (!response.ok) {
      requestsContainer.innerHTML = `

        <p class="empty">

          ${data.message || "Failed to load requests"}

        </p>

      `;

      return;
    }

    if (!data || data.length === 0) {
      requestsContainer.innerHTML = `

        <p class="empty">

          No blood requests found.

        </p>

      `;

      return;
    }

    requestsContainer.innerHTML = "";

    data.forEach((bloodRequest) => {
      const card = document.createElement("div");

      card.className = "request-card";

      const donors = bloodRequest.matched_donors || [];

      const validDonors = donors.filter(
        (donor) =>
          donor.latitude !== null &&
          donor.latitude !== undefined &&
          donor.longitude !== null &&
          donor.longitude !== undefined &&
          !isNaN(parseFloat(donor.latitude)) &&
          !isNaN(parseFloat(donor.longitude)),
      );
      const hospitalLat = bloodRequest.hospital_latitude;
      const hospitalLng = bloodRequest.hospital_longitude;

      // =================================================
      // DONOR CARDS
      // =================================================

      const donorsHTML =
        donors.length > 0
          ? donors

              .map((match) => {
                const donor = match.donor;

                const donorResponse = match.donor_response || "Pending";

                const distance =
                  match.distance_km != null
                    ? `${Number(match.distance_km).toFixed(2)} km`
                    : "Unavailable";

                const rankingScore =
                  match.ai_score != null
                    ? Number(match.ai_score).toFixed(2)
                    : "N/A";

                const responseProbability =
                  match.response_probability != null
                    ? `${match.response_probability}%`
                    : "N/A";

                const hasLocation =
                  donor.latitude != null && donor.longitude != null;

                return `

                    <div class="donor-card">


                      <div class="donor-card-header">


                        <h4>

                          🩸 Donor #${donor.donor_id}

                        </h4>


                        <span

                          class="response-status

                          ${getResponseClass(donorResponse)}"

                        >

                          ${donorResponse}

                        </span>


                      </div>


                      <div class="donor-details">


                        <p>

                          <strong>

                            Blood Group

                          </strong>


                          <span>

                            ${donor.blood_group || "N/A"}

                          </span>

                        </p>


                        <p>

                          <strong>

                            Distance

                          </strong>


                          <span>

                            ${distance}

                          </span>

                        </p>


                        <p>

                          <strong>

                            Ranking Score

                          </strong>


                          <span>

                            ${rankingScore}

                          </span>

                        </p>


                        <p>

                          <strong>

                            Response Probability

                          </strong>


                          <span>

                            ${responseProbability}

                          </span>

                        </p>


                      </div>


                      ${
                        hasLocation
                          ? `

                    <button
class="view-all-map-button"
onclick="viewAllDonorsOnMap(
${bloodRequest.request_id},
${bloodRequest.hospital_latitude},
${bloodRequest.hospital_longitude}
)"
>
🗺️ View All on Map
</button>
                          `
                          : `

                            <p

                              class="location-unavailable"

                            >

                              📍 Location unavailable

                            </p>

                          `
                      }


                    </div>

                  `;
              })

              .join("")
          : `

              <p class="no-donors">

                No matched donors yet.

              </p>

            `;

      // =================================================
      // REQUEST CARD
      // =================================================

      card.innerHTML = `


        <div class="request-card-header">


          <div>


            <h3>

              Request #${bloodRequest.request_id}

            </h3>


            <span

              class="request-status

              ${getStatusClass(bloodRequest.status)}"

            >

              ${bloodRequest.status}

            </span>


          </div>


          <span class="request-date">

            ${bloodRequest.request_time || "N/A"}

          </span>


        </div>


        <div class="request-details">


          <div>

            <strong>

              Blood Group

            </strong>


            <span>

              ${bloodRequest.blood_group}

            </span>

          </div>


          <div>

            <strong>

              Units Needed

            </strong>


            <span>

              ${bloodRequest.units_needed}

            </span>

          </div>


          <div>

            <strong>

              Emergency Level

            </strong>


            <span>

              ${bloodRequest.emergency_level}

            </span>

          </div>


<div>

    <strong>Hospital</strong>

    <span>${bloodRequest.hospital_name}</span>

</div>

<div>

    <strong>Location</strong>

    <span>

        ${bloodRequest.hospital_name}

        <br>

        (${bloodRequest.hospital_latitude},
        ${bloodRequest.hospital_longitude})

    </span>

</div>


        </div>


        <div class="matched-donors">


          <div class="matched-donors-header">


            <h3>

              Matched Donors

            </h3>


            ${
              validDonors.length > 0
                ? `

                  <button

                    class="view-all-map-button"

                    onclick="viewAllDonorsOnMap(

                      ${bloodRequest.request_id}

                    )"

                  >

                    🗺️ View All on Map

                  </button>

                `
                : ""
            }


          </div>


          ${donorsHTML}


        </div>


        ${
          bloodRequest.status === "Pending"
            ? `

              <button

                class="cancel-button"

                onclick="cancelRequest(

                  ${bloodRequest.request_id}

                )"

              >

                Cancel Request

              </button>

            `
            : ""
        }


      `;

      requestsContainer.appendChild(card);
    });
  } catch (error) {
    console.error(
      "My Requests Error:",

      error,
    );

    requestsContainer.innerHTML = `

      <p class="empty">

        Unable to connect to backend.

      </p>

    `;
  }
}

// =====================================================
// VIEW ALL DONORS ON MAP
// =====================================================
function viewAllDonorsOnMap(requestId, hospitalLat, hospitalLng) {
  localStorage.setItem("selected_request_id", requestId);

  localStorage.setItem("hospital_latitude", hospitalLat);

  localStorage.setItem("hospital_longitude", hospitalLng);

  localStorage.removeItem("selected_donor_id");

  window.location.href = "donor-map.html";
}

// =====================================================
// VIEW SINGLE DONOR ON MAP
// =====================================================
function viewDonorOnMap(requestId, donorId) {
  localStorage.setItem("selected_request_id", requestId);

  localStorage.setItem("selected_donor_id", donorId);

  window.location.href = "donor-map.html";
}

// =====================================================
// RESPONSE STATUS CLASS
// =====================================================

function getResponseClass(response) {
  if (!response) {
    return "pending";
  }

  return response

    .toLowerCase()

    .replace(/\s+/g, "-");
}

// =====================================================
// REQUEST STATUS CLASS
// =====================================================

function getStatusClass(status) {
  if (!status) {
    return "";
  }

  return status

    .toLowerCase()

    .replace(/\s+/g, "-");
}

// =====================================================
// CANCEL REQUEST
// =====================================================

async function cancelRequest(requestId) {
  const confirmCancel = confirm(
    "Are you sure you want to cancel this blood request?",
  );

  if (!confirmCancel) {
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/api/requests/${requestId}/cancel`,

      {
        method: "PATCH",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const result = await response.json();

    if (!response.ok) {
      alert(result.message || "Failed to cancel request");

      return;
    }

    alert("Blood request cancelled successfully");

    loadMyRequests();
  } catch (error) {
    console.error(
      "Cancel Request Error:",

      error,
    );

    alert("Unable to connect to backend");
  }
}
// =====================================================
// COMPLETE DONATION
// =====================================================

async function completeDonation(requestId) {
  const confirmComplete = confirm(
    "Confirm that the blood donation has been completed?",
  );

  if (!confirmComplete) {
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/api/requests/${requestId}/complete`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const data = await response.json();

    if (!response.ok) {
      alert(data.message);
      return;
    }

    alert(data.message);

    loadMyRequests();
  } catch (error) {
    console.error(error);

    alert("Unable to connect to backend.");
  }
}

// =====================================================
// START
// =====================================================

loadMyRequests();

function goBackToDashboard() {
  const role = localStorage.getItem("role");

  if (role === "DONOR") {
    window.location.href = "donor-dashboard.html";
  } else if (role === "PATIENT") {
    window.location.href = "patient-dashboard.html";
  } else if (role === "ADMIN") {
    window.location.href = "admin-dashboard.html";
  } else {
    window.location.href = "login.html";
  }
}