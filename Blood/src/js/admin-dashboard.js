const API_URL = "http://127.0.0.1:5000/api";
const ADMIN_API_URL = `${API_URL}/admin`;

const token = localStorage.getItem("token");

if (!token) {
  window.location.href = "login.html";
}

// Profile Dropdown Actions
document.addEventListener("DOMContentLoaded", () => {
  const userStr = localStorage.getItem("user");
  if (userStr) {
    const user = JSON.parse(userStr);
    const nameEl = document.getElementById("headerProfileName");
    const roleEl = document.getElementById("headerProfileRole");
    if (nameEl) nameEl.textContent = user.full_name || user.email || "User";
    if (roleEl) roleEl.textContent = user.role || "Role";
  }

  const trigger = document.getElementById("profileTrigger");
  const menu = document.getElementById("profileDropdownMenu");
  if (trigger && menu) {
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      menu.classList.toggle("show");
    });
    document.addEventListener("click", (e) => {
      if (!trigger.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.remove("show");
      }
    });
  }

  const dropdownLogoutBtn = document.getElementById("dropdownLogoutBtn");
  if (dropdownLogoutBtn) {
    dropdownLogoutBtn.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "login.html";
    });
  }
});
document
  .getElementById("refreshBtn")
  .addEventListener("click", initializeDashboard);
// ================================
// COMMON FETCH
// ================================

async function api(url) {
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    alert(data.message);

    throw new Error(data.message);
  }

  return data;
}

// ================================
// DASHBOARD SUMMARY
// ================================

async function loadSummary() {
  const data = await api(`${ADMIN_API_URL}/dashboard`);

  document.getElementById("summaryCards").innerHTML = `
    <div class="stat-card-admin">
        <div class="stat-header">
            <span class="stat-label">Total Users</span>
            <span class="stat-icon blue"><i class="fas fa-users"></i></span>
        </div>
        <span class="stat-number">${data.total_users}</span>
    </div>
    
    <div class="stat-card-admin">
        <div class="stat-header">
            <span class="stat-label">Donors</span>
            <span class="stat-icon red"><i class="fas fa-user-md"></i></span>
        </div>
        <span class="stat-number">${data.total_donors}</span>
    </div>
    
    <div class="stat-card-admin">
        <div class="stat-header">
            <span class="stat-label">Blood Requests</span>
            <span class="stat-icon gold"><i class="fas fa-hand-holding-heart"></i></span>
        </div>
        <span class="stat-number">${data.total_requests}</span>
    </div>
    
    <div class="stat-card-admin">
        <div class="stat-header">
            <span class="stat-label">Lives Saved / Donations</span>
            <span class="stat-icon green"><i class="fas fa-heart"></i></span>
        </div>
        <span class="stat-number">${data.total_donations}</span>
    </div>
  `;
}

// ================================
// USERS
// ================================

async function loadUsers() {
  const users = await api(`${ADMIN_API_URL}/users`);

  let html = `
    <table class="user-table">
        <thead>
            <tr>
                <th>User</th>
                <th>Type</th>
                <th>Status</th>
                <th style="text-align:right;">Action</th>
            </tr>
        </thead>
        <tbody>
  `;

  users.forEach((user) => {
    const initials = user.full_name ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'U';
    const typeClass = user.role.toLowerCase();
    
    html += `
        <tr>
            <td>
                <div class="user-cell">
                    <div class="avatar-sm">${initials}</div>
                    <div>
                        <div class="user-name">${user.full_name || 'N/A'}</div>
                        <div class="user-email">${user.email}</div>
                    </div>
                </div>
            </td>
            <td><span class="type-tag ${typeClass}">${user.role}</span></td>
            <td><span class="status-badge-sm ${user.active ? 'active' : 'blocked'}">${user.active ? 'Active' : 'Blocked'}</span></td>
            <td style="text-align:right;">
                <button class="action-btn edit" onclick="toggleUser(${user.user_id}, ${user.active})" title="${user.active ? 'Block' : 'Unblock'}">
                    <i class="fas ${user.active ? 'fa-ban' : 'fa-check'}"></i>
                </button>
                <button class="action-btn delete" onclick="deleteUser(${user.user_id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
  });

  html += `
        </tbody>
    </table>
  `;

  document.getElementById("usersTable").innerHTML = html;
}

// ================================
// BLOCK / UNBLOCK USER
// ================================

async function toggleUser(id, active) {
  const endpoint = active ? "block" : "unblock";

  await fetch(
    `${ADMIN_API_URL}/users/${id}/${endpoint}`,

    {
      method: "PATCH",

      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  loadUsers();
}

// ================================
// DELETE USER
// ================================

async function deleteUser(id) {
  if (!confirm("Delete user?")) return;

  const response = await fetch(`${ADMIN_API_URL}/users/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadUsers();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete user.");
}
// ================================
// DONORS
// ================================

async function loadDonors() {

    const donors = await api(
        `${ADMIN_API_URL}/donors`
    );

    let html = `

<table>

<tr>

<th>ID</th>
<th>Blood</th>
<th>Age</th>
<th>Phone</th>
<th>Availability</th>
<th>Reliability</th>
<th>Action</th>

</tr>

`;

    donors.forEach(donor => {

        html += `

<tr>

<td>${donor.donor_id}</td>

<td>${donor.blood_group}</td>

<td>${donor.age}</td>

<td>${donor.phone}</td>

<td>${donor.availability ? "Available" : "Unavailable"}</td>

<td>${donor.reliability_score}</td>

<td>

<button
class="delete-btn"
onclick="deleteDonor(${donor.donor_id})">

Delete

</button>

</td>

</tr>

`;

    });

    html += "</table>";

    document.getElementById(
        "donorsTable"
    ).innerHTML = html;

}


// ================================
// DELETE DONOR
// ================================

async function deleteDonor(id) {
  if (!confirm("Delete donor?")) return;

  const response = await fetch(`${ADMIN_API_URL}/donors/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadDonors();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete donor.");
}


// ================================
// PATIENTS
// ================================

async function loadPatients() {

    const patients = await api(
        `${ADMIN_API_URL}/patients`
    );

    let html = `

<table>

<tr>

<th>ID</th>
<th>Blood</th>
<th>Age</th>
<th>Hospital</th>
<th>Action</th>

</tr>

`;

    patients.forEach(patient => {

        html += `

<tr>

<td>${patient.patient_id}</td>

<td>${patient.blood_group}</td>

<td>${patient.age}</td>

<td>${patient.hospital_name}</td>

<td>

<button
class="delete-btn"
onclick="deletePatient(${patient.patient_id})">

Delete

</button>
</td>

</tr>

`;

    });

    html += "</table>";

    document.getElementById(
        "patientsTable"
    ).innerHTML = html;

}


// ================================
// DELETE PATIENT
// ================================

async function deletePatient(id) {
  if (!confirm("Delete patient?")) return;

  const response = await fetch(`${ADMIN_API_URL}/patients/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadPatients();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete patient.");
}


// ================================
// BLOOD REQUESTS
// ================================

async function loadRequests() {

    const requests = await api(
        `${ADMIN_API_URL}/requests`
    );

    let html = `

<table>

<tr>

<th>ID</th>
<th>Blood</th>
<th>Units</th>
<th>Status</th>
<th>Emergency</th>
<th>Action</th>

</tr>

`;

    requests.forEach(req => {

        html += `

<tr>

<td>${req.request_id}</td>

<td>${req.blood_group}</td>

<td>${req.units_needed}</td>

<td>${req.status}</td>

<td>${req.emergency_level}</td>

<td>

<button
class="delete-btn"
onclick="deleteRequest(${req.request_id})">

Delete

</button>

</td>

</tr>

`;

    });

    html += "</table>";

    document.getElementById(
        "requestsTable"
    ).innerHTML = html;

}


// ================================
// DELETE REQUEST
// ================================

async function deleteRequest(id) {
  if (!confirm("Delete Request?")) return;

  const response = await fetch(`${ADMIN_API_URL}/requests/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadRequests();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete request.");
}
// ================================
// DONATIONS
// ================================

async function loadDonations() {

    const donations = await api(
        `${ADMIN_API_URL}/donations`
    );

    let html = `

<table>

<tr>

<th>ID</th>
<th>Donor</th>
<th>Patient</th>
<th>Date</th>
<th>Units</th>
<th>Action</th>
<th>Status</th>

</tr>

`;

    donations.forEach(donation => {

        html += `

<tr>

<td>${donation.donation_id}</td>

<td>${donation.donor_id}</td>

<td>${donation.patient_id}</td>

<td>${donation.donation_date}</td>

<td>${donation.units_donated}</td>
<td>${donation.donation_status}</td>

<td>

<button
class="delete-btn"
onclick="deleteDonation(${donation.donation_id})">

Delete

</button>

</td>

</tr>

`;

    });

    html += "</table>";

    document.getElementById(
        "donationsTable"
    ).innerHTML = html;

}


// ================================
// DELETE DONATION
// ================================

async function deleteDonation(id) {
  if (!confirm("Delete Donation?")) return;

  const response = await fetch(`${ADMIN_API_URL}/donations/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadDonations();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete donation.");
}


// ================================
// MATCHES
// ================================

async function loadMatches() {

    const matches = await api(
        `${ADMIN_API_URL}/matches`
    );

    let html = `

<table>

<tr>

<th>ID</th>
<th>Request</th>
<th>Donor</th>
<th>Score</th>
<th>Distance</th>
<th>Status</th>
<th>Action</th>

</tr>

`;

    matches.forEach(match => {

        html += `

<tr>

<td>${match.match_id}</td>

<td>${match.request_id}</td>

<td>${match.donor_id}</td>

<td>${match.ranking_score}</td>

<td>${match.distance_km} km</td>

<td>${match.donor_response}</td>

<td>
<button
class="delete-btn"
onclick="deleteMatch(${match.match_id})">

Delete

</button>

</td>

</tr>

`;

    });

    html += "</table>";

    document.getElementById(
        "matchesTable"
    ).innerHTML = html;

}


// ================================
// DELETE MATCH
// ================================

async function deleteMatch(id) {
  if (!confirm("Delete Match?")) return;

  const response = await fetch(`${ADMIN_API_URL}/matches/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadMatches();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete match.");
}


// ================================
// ANALYTICS
// ================================

async function loadAnalytics() {

    const analytics = await api(
        `${ADMIN_API_URL}/analytics`
    );

    document.getElementById(
        "analyticsCards"
    ).innerHTML = `

<div class="summary-grid">

<div class="summary-card">

<h3>Total Users</h3>

<h2>${analytics.users}</h2>

</div>

<div class="card">

<h3>Total Donors</h3>

<h2>${analytics.donors}</h2>

</div>

<div class="card">

<h3>Total Patients</h3>

<h2>${analytics.patients}</h2>

</div>

<div class="card">

<h3>Total Requests</h3>

<h2>${analytics.requests}</h2>

</div>

<div class="card">

<h3>Pending</h3>

<h2>${analytics.pending_requests}</h2>

</div>

<div class="card">

<h3>Matched</h3>

<h2>${analytics.matched_requests}</h2>

</div>

<div class="card">

<h3>Accepted</h3>

<h2>${analytics.accepted_requests}</h2>

</div>

<div class="card">

<h3>Completed</h3>

<h2>${analytics.completed_requests}</h2>

</div>

<div class="card">

<h3>Cancelled</h3>

<h2>${analytics.cancelled_requests}</h2>

</div>

<div class="card">

<h3>Donations</h3>

<h2>${analytics.total_donations}</h2>

</div>

</div>

`;

}


// ================================
// REPORTS
// ================================

//document.getElementById(
  //  "downloadDonorReport"
//).onclick = () => {

   // window.open(
     //   `${ADMIN_API_URL}/reports/donors`,
       // "_blank"
    //);

//};
// ================================
// REPORTS
// ================================

async function downloadReport(url, filename) {

    const response = await fetch(url, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    if (!response.ok) {
        alert("Failed to download report");
        return;
    }

    const blob = await response.blob();

    const link = document.createElement("a");

    link.href = URL.createObjectURL(blob);

    link.download = filename;

    link.click();
}

document.getElementById("downloadDonorReport").onclick = () => {
    downloadReport(`${ADMIN_API_URL}/reports/donors`, "donor_report.csv");
};

document.getElementById("downloadPatientReport").onclick = () => {
    downloadReport(`${ADMIN_API_URL}/reports/patients`, "patient_report.csv");
};

document.getElementById("downloadRequestReport").onclick = () => {
    downloadReport(`${ADMIN_API_URL}/reports/requests`, "request_report.csv");
};

document.getElementById("downloadDonationReport").onclick = () => {
    downloadReport(`${ADMIN_API_URL}/reports/donations`, "donation_report.csv");
};
// ================================
// INITIAL LOAD
// ================================

async function initializeDashboard() {
  try {
    await loadSummary();

    await loadUsers();

    await loadDonors();

    await loadPatients();

    await loadRequests();

    await loadDonations();

    await loadMatches();

    await loadAnalytics();
  } catch (error) {
    console.error(error);

    alert("Unable to load admin dashboard.");
  }
}


initializeDashboard();


// ================================
// AUTO REFRESH
// ================================
document.getElementById("refreshBtn").addEventListener("click", () => {
  initializeDashboard();
});
setInterval(

    initializeDashboard,

    30000

);