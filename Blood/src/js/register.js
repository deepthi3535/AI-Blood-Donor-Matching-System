console.log("REGISTER JS LOADED");

const API_URL = "http://127.0.0.1:5000";

const registerForm = document.getElementById("registerForm");
const role = document.getElementById("role");
const donorFields = document.getElementById("donorFields");
const hospitalFields = document.getElementById("hospitalFields");

// =============================
// SHOW / HIDE ROLE SPECIFIC FIELDS
// =============================
console.log("ROLE EVENT ATTACHED");

role.addEventListener("change", function () {
  console.log("ROLE CHANGED:", role.value);

  const donorInputs = donorFields.querySelectorAll("input, select");
  const hospitalInputs = hospitalFields.querySelectorAll("input");

  if (role.value === "DONOR") {
    donorFields.style.display = "block";
    hospitalFields.style.display = "none";

    donorInputs.forEach((input) => (input.required = true));
    hospitalInputs.forEach((input) => (input.required = false));
  } else if (role.value === "HOSPITAL") {
    donorFields.style.display = "none";
    hospitalFields.style.display = "block";

    donorInputs.forEach((input) => (input.required = false));
    hospitalInputs.forEach((input) => (input.required = true));
  } else {
    donorFields.style.display = "none";
    hospitalFields.style.display = "none";

    donorInputs.forEach((input) => {
      input.required = false;
      if (input.type !== "hidden") {
        input.value = "";
      }
    });

    hospitalInputs.forEach((input) => {
      input.required = false;
      if (input.type !== "hidden") {
        input.value = "";
      }
    });
  }
});
// =============================
// GET CURRENT LOCATION
// =============================
document.getElementById("getLocation").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Geolocation not supported.");

    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("latitude").value = position.coords.latitude;

      document.getElementById("longitude").value = position.coords.longitude;

      alert("Location Captured Successfully");
    },

    () => {
      alert("Unable to fetch location");
    },
  );
});

// =============================
// GET HOSPITAL LOCATION
// =============================
document.getElementById("getHospitalLocation").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Geolocation not supported.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("hospital_latitude").value = position.coords.latitude;
      document.getElementById("hospital_longitude").value = position.coords.longitude;
      alert("Hospital Location Captured Successfully");
    },
    () => {
      alert("Unable to fetch hospital location");
    },
  );
});

// =============================
// REGISTER
// =============================
registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const full_name = document.getElementById("full_name").value.trim();

  const email = document.getElementById("email").value.trim();

  const phone = document.getElementById("phone").value.trim();

  const password = document.getElementById("password").value;

  const confirm_password = document.getElementById("confirm_password").value;

  if (password !== confirm_password) {
    alert("Passwords do not match");

    return;
  }

  let userData = {
    full_name,

    email,

    phone,

    password,

    role: role.value,
  };

  // =============================
  // DONOR EXTRA DATA
  // =============================

  if (role.value === "DONOR") {
    userData.age = parseInt(document.getElementById("age").value);

    userData.gender = document.getElementById("gender").value;
    userData.weight = parseFloat(document.getElementById("weight").value);

    userData.blood_group = document.getElementById("blood_group").value;

    userData.address = document.getElementById("address").value.trim();
    userData.latitude = parseFloat(document.getElementById("latitude").value);

    userData.longitude = parseFloat(document.getElementById("longitude").value);


    userData.availability = true;
    if (
      !userData.age ||
      !userData.gender ||
      isNaN(userData.weight) ||
      userData.weight < 50 ||
      !userData.blood_group ||
      !userData.address ||
      isNaN(userData.latitude) ||
      isNaN(userData.longitude)
    ) {
      alert("Please fill all donor details. Weight must be at least 50 kg.");
      return;
    }
  }

  // =============================
  // HOSPITAL EXTRA DATA
  // =============================
  if (role.value === "HOSPITAL") {
    userData.address = document.getElementById("hospital_address").value.trim();
    userData.latitude = parseFloat(document.getElementById("hospital_latitude").value);
    userData.longitude = parseFloat(document.getElementById("hospital_longitude").value);
    userData.hospital_name = full_name;

    if (
      !userData.address ||
      isNaN(userData.latitude) ||
      isNaN(userData.longitude)
    ) {
      alert("Please enter the hospital address and capture its location.");
      return;
    }
  }

  console.log(userData);

  try {
    const response = await fetch(
      API_URL + "/api/auth/register",

      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify(userData),
      },
    );

    const result = await response.json();

    if (response.ok) {
      if (userData.role === "DONOR" || userData.role === "PATIENT" || userData.role === "HOSPITAL") {
        alert(result.message || "Registration successful. Please verify your email.");
        document.getElementById("registerCard").style.display = "none";
        document.getElementById("otpSection").style.display = "block";
        document.getElementById("otpEmailDisplay").textContent = userData.email;
        startResendCooldown();
      } else {
        alert(result.message);
        window.location.href = "login.html";
      }
    } else {
      alert(result.message);
    }
  } catch (err) {
    console.log(err);

    alert("Unable to connect backend.");
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
    const response = await fetch(`${API_URL}/api/auth/verify-email`, {
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
    console.error(err);
    alert("Unable to verify OTP.");
  }
});

document.getElementById("resendOtpBtn").addEventListener("click", async () => {
  if (cooldownTime > 0) return;
  const email = document.getElementById("otpEmailDisplay").textContent.trim();

  try {
    const response = await fetch(`${API_URL}/api/auth/resend-otp`, {
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
    console.error(err);
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
