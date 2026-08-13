console.log("REGISTER JS LOADED");

const API_URL = "http://127.0.0.1:5000";

const registerForm = document.getElementById("registerForm");
const role = document.getElementById("role");
const donorFields = document.getElementById("donorFields");

// =============================
// SHOW / HIDE DONOR FIELDS
// =============================
console.log("ROLE EVENT ATTACHED");

role.addEventListener("change", function () {
  console.log("ROLE CHANGED:", role.value);

  const donorInputs = donorFields.querySelectorAll("input, select");

  if (role.value === "DONOR") {
    donorFields.style.display = "block";

    donorInputs.forEach((input) => (input.required = true));
  } else {
    donorFields.style.display = "none";

    donorInputs.forEach((input) => {
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
      alert(result.message);

      window.location.href = "login.html";
    } else {
      alert(result.message);
    }
  } catch (err) {
    console.log(err);

    alert("Unable to connect backend.");
  }
});
