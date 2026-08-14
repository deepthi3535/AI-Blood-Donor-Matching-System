const API_URL = "http://127.0.0.1:5000/api";

const token = localStorage.getItem("token");
let user = JSON.parse(localStorage.getItem("user")) || {};

if (!token || !user) {
  window.location.href = "login.html";
}

// Global page fields elements
const profileForm = document.getElementById("profileForm");
const patientProfileForm = document.getElementById("patientProfileForm");
const backToDashBtn = document.getElementById("backToDashBtn");
const updateLocationBtn = document.getElementById("updateLocationBtn");
const getLocationButton = document.getElementById("getLocationButton");
const locationMessage = document.getElementById("locationMessage");
const profileMessage = document.getElementById("profileMessage");

let patientId = localStorage.getItem("patient_id");
let donorId = null;

// Determine role and toggle fields visibility
function initFields() {
  const patientFields = document.getElementById("patientFields");
  const donorFields = document.getElementById("donorFields");

  if (user.role === "PATIENT") {
    if (patientFields) patientFields.style.display = "block";
    if (donorFields) donorFields.style.display = "none";
  } else if (user.role === "DONOR") {
    if (patientFields) patientFields.style.display = "none";
    if (donorFields) donorFields.style.display = "block";
  }
}

// Load profile values from backend dashboard endpoints
async function loadProfile() {
  initFields();

  // Primary user account details
  const nameInput = document.getElementById("full_name");
  const emailInput = document.getElementById("email");
  const phoneInput = document.getElementById("phone");

  if (nameInput) nameInput.value = user.full_name || "";
  if (emailInput) emailInput.value = user.email || "";
  if (phoneInput) phoneInput.value = user.phone || "";

  try {
    let response, data;
    if (user.role === "PATIENT") {
      response = await fetch(`${API_URL}/patients/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      data = await response.json();
      if (response.ok && data.patient) {
        patientId = data.patient.patient_id;
        localStorage.setItem("patient_id", patientId);

        if (nameInput && data.patient.full_name) nameInput.value = data.patient.full_name;
        if (emailInput && data.patient.email) emailInput.value = data.patient.email;
        if (phoneInput && data.patient.phone) phoneInput.value = data.patient.phone;

        if (document.getElementById("blood_group")) document.getElementById("blood_group").value = data.patient.blood_group || "A+";
        if (document.getElementById("age")) document.getElementById("age").value = data.patient.age || "";
        if (document.getElementById("gender")) document.getElementById("gender").value = data.patient.gender || "Male";
        if (document.getElementById("hospital_name")) document.getElementById("hospital_name").value = data.patient.hospital_name || "";
        if (document.getElementById("latitude")) document.getElementById("latitude").value = data.patient.latitude || "";
        if (document.getElementById("longitude")) document.getElementById("longitude").value = data.patient.longitude || "";
      }
    } else if (user.role === "DONOR") {
      response = await fetch(`${API_URL}/donors/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      data = await response.json();
      if (response.ok && data.donor) {
        donorId = data.donor.donor_id;

        if (nameInput && data.donor.full_name) nameInput.value = data.donor.full_name;
        if (emailInput && data.donor.email) emailInput.value = data.donor.email;
        if (phoneInput && data.donor.phone) phoneInput.value = data.donor.phone;

        if (document.getElementById("blood_group")) document.getElementById("blood_group").value = data.donor.blood_group || "A+";
        if (document.getElementById("age")) document.getElementById("age").value = data.donor.age || "";
        if (document.getElementById("gender")) document.getElementById("gender").value = data.donor.gender || "Male";
        if (document.getElementById("address")) document.getElementById("address").value = data.donor.address || "";
        if (document.getElementById("donorWeight")) document.getElementById("donorWeight").value = data.donor.weight || "";
        if (document.getElementById("availability")) document.getElementById("availability").checked = data.donor.availability;
        if (document.getElementById("latitude")) document.getElementById("latitude").value = data.donor.latitude || "";
        if (document.getElementById("longitude")) document.getElementById("longitude").value = data.donor.longitude || "";
      }
    }
  } catch (err) {
    console.error("Error loading profile:", err);
  }
}

// Location Capturer
function captureLocation() {
  if (!navigator.geolocation) {
    if (locationMessage) locationMessage.textContent = "Geolocation is not supported.";
    return;
  }
  if (locationMessage) locationMessage.textContent = "Locating...";

  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (document.getElementById("latitude")) document.getElementById("latitude").value = position.coords.latitude;
      if (document.getElementById("longitude")) document.getElementById("longitude").value = position.coords.longitude;
      if (locationMessage) locationMessage.textContent = "Location updated successfully.";
    },
    (error) => {
      if (locationMessage) locationMessage.textContent = "Error capturing location: " + error.message;
    }
  );
}

if (updateLocationBtn) updateLocationBtn.addEventListener("click", captureLocation);
if (getLocationButton) getLocationButton.addEventListener("click", captureLocation);

// Form submission handler
async function handleFormSubmit(e) {
  e.preventDefault();
  profileMessage.textContent = "Saving...";

  const nameValue = document.getElementById("full_name") ? document.getElementById("full_name").value : "";
  const emailValue = document.getElementById("email") ? document.getElementById("email").value : "";
  const phoneValue = document.getElementById("phone") ? document.getElementById("phone").value : "";

  const payload = {
    full_name: nameValue,
    email: emailValue,
    phone: phoneValue,
    blood_group: document.getElementById("blood_group").value,
    age: Number(document.getElementById("age").value),
    gender: document.getElementById("gender").value,
    latitude: document.getElementById("latitude").value ? Number(document.getElementById("latitude").value) : null,
    longitude: document.getElementById("longitude").value ? Number(document.getElementById("longitude").value) : null,
  };

  let method = "PUT";
  let endpoint = "";

  if (user.role === "PATIENT") {
    // If patientProfileForm exists, we do first-time creation (POST), otherwise edit (PUT)
    if (patientProfileForm) {
      method = "POST";
      endpoint = `${API_URL}/patients/`;
    } else {
      method = "PUT";
      endpoint = `${API_URL}/patients/${patientId}`;
    }
    payload.hospital_name = document.getElementById("hospital_name").value;
  } else if (user.role === "DONOR") {
    method = "PUT";
    endpoint = `${API_URL}/donors/${donorId}`;
    payload.address = document.getElementById("address").value;
    payload.weight = Number(document.getElementById("donorWeight").value);
    payload.availability = document.getElementById("availability").checked;
  }

  try {
    const response = await fetch(endpoint, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (response.ok) {
      profileMessage.textContent = "Profile updated successfully!";
      profileMessage.style.color = "var(--success)";
      
      // Update local storage user details
      user.full_name = nameValue;
      user.email = emailValue;
      user.phone = phoneValue;
      localStorage.setItem("user", JSON.stringify(user));

      setTimeout(goBackToDashboard, 1500);
    } else {
      profileMessage.textContent = result.message || "Failed to update profile.";
      profileMessage.style.color = "var(--danger)";
    }
  } catch (error) {
    console.error("Save Error:", error);
    profileMessage.textContent = "Error connecting to server.";
    profileMessage.style.color = "var(--danger)";
  }
}

if (profileForm) profileForm.addEventListener("submit", handleFormSubmit);
if (patientProfileForm) patientProfileForm.addEventListener("submit", handleFormSubmit);

// Back to Dashboard routing
function goBackToDashboard() {
  if (user.role === "DONOR") {
    window.location.href = "donor-dashboard.html";
  } else if (user.role === "PATIENT") {
    window.location.href = "patient-dashboard.html";
  } else if (user.role === "HOSPITAL") {
    window.location.href = "hospital-dashboard.html";
  } else {
    window.location.href = "login.html";
  }
}

if (backToDashBtn) {
  backToDashBtn.addEventListener("click", goBackToDashboard);
}

// Run initial load
loadProfile();
