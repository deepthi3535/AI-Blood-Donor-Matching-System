console.log("REGISTER JS LOADED");

const API_URL = "http://127.0.0.1:5000/api";

const registerForm = document.getElementById("registerForm");
const donorFields = document.getElementById("donorFields");
const patientFields = document.getElementById("patientFields");
const hospitalFields = document.getElementById("hospitalFields");

// =============================
// USER TYPE TOGGLE BUTTONS
// =============================
document.querySelectorAll('.type-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    
    const type = this.dataset.type;
    registerForm.dataset.userType = type;
    
    // Toggle field visibility
    donorFields.style.display = type === 'donor' ? 'block' : 'none';
    patientFields.style.display = type === 'patient' ? 'block' : 'none';
    hospitalFields.style.display = type === 'hospital' ? 'block' : 'none';
    
    // Toggle required fields
    const donorInputs = donorFields.querySelectorAll("input, select");
    const patientInputs = patientFields.querySelectorAll("input, select");
    const hospitalInputs = hospitalFields.querySelectorAll("input, textarea");
    
    donorInputs.forEach(input => input.required = (type === 'donor' && input.id !== 'terms'));
    patientInputs.forEach(input => input.required = (type === 'patient'));
    hospitalInputs.forEach(input => input.required = (type === 'hospital'));
  });
});

// Setup default required fields
const initialDonorInputs = donorFields.querySelectorAll("input, select");
initialDonorInputs.forEach(input => input.required = (input.id !== 'terms'));

// =============================
// GET GEOLOCATION FOR DONOR
// =============================
document.getElementById("getLocation").addEventListener("click", () => {
  const status = document.getElementById("locationStatus");
  if (!navigator.geolocation) {
    status.textContent = "Geolocation is not supported.";
    return;
  }
  status.textContent = "Getting location...";

  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("latitude").value = position.coords.latitude;
      document.getElementById("longitude").value = position.coords.longitude;
      status.innerHTML = `✅ Location captured: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
    },
    (error) => {
      status.textContent = `❌ ${error.message}`;
    }
  );
});

// =============================
// GET GEOLOCATION FOR HOSPITAL
// =============================
document.getElementById("getHospitalLocation").addEventListener("click", () => {
  const status = document.getElementById("hospitalLocationStatus");
  if (!navigator.geolocation) {
    status.textContent = "Geolocation is not supported.";
    return;
  }
  status.textContent = "Getting location...";

  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("hospital_latitude").value = position.coords.latitude;
      document.getElementById("hospital_longitude").value = position.coords.longitude;
      status.innerHTML = `✅ Location captured: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
    },
    (error) => {
      status.textContent = `❌ ${error.message}`;
    }
  );
});

// =============================
// REGISTRATION HANDLER
// =============================
registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const userType = registerForm.dataset.userType || "donor";
  const firstName = document.getElementById("firstName").value.trim();
  const lastName = document.getElementById("lastName").value.trim();
  const full_name = `${firstName} ${lastName}`;
  const email = document.getElementById("email").value.trim();
  const phone = document.getElementById("phone").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  if (password !== confirmPassword) {
    alert("Passwords do not match!");
    return;
  }

  const userData = {
    full_name,
    email,
    phone,
    password,
    role: userType.toUpperCase()
  };

  // Donor-specific payload
  if (userType === "donor") {
    userData.age = parseInt(document.getElementById("dob").value);
    userData.gender = document.getElementById("gender").value;
    userData.weight = parseFloat(document.getElementById("weight").value);
    userData.blood_group = document.getElementById("bloodGroup").value;
    userData.address = document.getElementById("address").value.trim();
    userData.latitude = document.getElementById("latitude").value ? parseFloat(document.getElementById("latitude").value) : null;
    userData.longitude = document.getElementById("longitude").value ? parseFloat(document.getElementById("longitude").value) : null;

    if (userData.latitude === null || userData.longitude === null) {
      alert("Please capture your location coordinate first.");
      return;
    }
  }

  // Patient-specific payload
  if (userType === "patient") {
    userData.blood_group = document.getElementById("patientBloodGroup").value;
    userData.hospital_name = document.getElementById("patientHospital").value.trim();
  }

  // Hospital-specific payload
  if (userType === "hospital") {
    userData.address = document.getElementById("hospitalAddress").value.trim();
    userData.latitude = document.getElementById("hospital_latitude").value ? parseFloat(document.getElementById("hospital_latitude").value) : null;
    userData.longitude = document.getElementById("hospital_longitude").value ? parseFloat(document.getElementById("hospital_longitude").value) : null;
    userData.hospital_name = full_name;

    if (userData.latitude === null || userData.longitude === null) {
      alert("Please capture hospital location coordinate first.");
      return;
    }
  }

  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    });

    const result = await response.json();

    if (response.ok) {
      if (userData.role !== "ADMIN") {
        alert(result.message || "Registration successful! Please verify your email.");
        document.getElementById("registerCard").style.display = "none";
        document.getElementById("otpSection").style.display = "block";
        document.getElementById("otpEmailDisplay").textContent = userData.email;
        startResendCooldown();
      } else {
        alert("Admin registration successful! Redirecting to login.");
        window.location.href = "login.html";
      }
    } else {
      alert(result.message || "Registration failed.");
    }
  } catch (err) {
    console.error("Register Error:", err);
    alert("Unable to connect to backend server.");
  }
});

// =============================
// OTP VERIFICATION STATE
// =============================
let cooldownTime = 0;
let cooldownInterval = null;

function startResendCooldown() {
  const resendBtn = document.getElementById("resendOtpBtn");
  const timerMsg = document.getElementById("resendTimerMessage");

  cooldownTime = 60;
  resendBtn.disabled = true;
  resendBtn.style.opacity = "0.5";
  resendBtn.style.cursor = "not-allowed";

  if (cooldownInterval) clearInterval(cooldownInterval);

  cooldownInterval = setInterval(() => {
    cooldownTime--;
    if (cooldownTime <= 0) {
      clearInterval(cooldownInterval);
      resendBtn.disabled = false;
      resendBtn.style.opacity = "1";
      resendBtn.style.cursor = "pointer";
      timerMsg.textContent = "";
    } else {
      timerMsg.textContent = `Resend available in ${cooldownTime} seconds.`;
    }
  }, 1000);
}

document.getElementById("otpForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const otp = document.getElementById("otpCode").value.trim();
  const email = document.getElementById("otpEmailDisplay").textContent.trim();

  try {
    const response = await fetch(`${API_URL}/auth/verify-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp })
    });
    const result = await response.json();
    if (response.ok) {
      alert(result.message || "Email verified successfully!");
      window.location.href = "login.html";
    } else {
      alert(result.message || "Invalid OTP.");
    }
  } catch (err) {
    console.error("Verification Error:", err);
    alert("Unable to verify OTP.");
  }
});

document.getElementById("resendOtpBtn").addEventListener("click", async () => {
  if (cooldownTime > 0) return;
  const email = document.getElementById("otpEmailDisplay").textContent.trim();

  try {
    const response = await fetch(`${API_URL}/auth/resend-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    const result = await response.json();
    if (response.ok) {
      alert(result.message || "New OTP sent!");
      startResendCooldown();
    } else {
      alert(result.message || "Failed to resend OTP.");
    }
  } catch (err) {
    console.error("Resend Error:", err);
    alert("Unable to resend OTP.");
  }
});

// Check if email query parameter is present on page load
const urlParams = new URLSearchParams(window.location.search);
const verifyEmailParam = urlParams.get("email");
if (verifyEmailParam) {
  document.getElementById("registerCard").style.display = "none";
  document.getElementById("otpSection").style.display = "block";
  document.getElementById("otpEmailDisplay").textContent = verifyEmailParam.trim();
  startResendCooldown();
}
