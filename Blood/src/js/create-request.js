const API_URL = "http://127.0.0.1:5000";

const requestForm = document.getElementById("requestForm");
const requestMessage = document.getElementById("requestMessage");

let selectedLatitude = null;
let selectedLongitude = null;

// -----------------------------
// Open Google Maps
// -----------------------------

document.getElementById("selectLocation").addEventListener("click", () => {
window.open("https://www.google.com/maps/search/hospitals", "_blank");

  alert(
    "Open Google Maps.\n\nRight Click your hospital location -> What's Here?\n\nCopy Latitude & Longitude and paste below.",
  );
});

// -----------------------------
// Submit Request
// -----------------------------

requestForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  requestMessage.textContent = "";

  const token = localStorage.getItem("token");

  if (!token) {
    requestMessage.textContent = "Please Login.";

    return;
  }


  selectedLatitude = parseFloat(
    document.getElementById("hospital_latitude").value,
  );

  selectedLongitude = parseFloat(
    document.getElementById("hospital_longitude").value,
  );

  if (isNaN(selectedLatitude) || isNaN(selectedLongitude)) {
    requestMessage.style.color = "red";

    requestMessage.textContent = "Please enter Hospital Latitude & Longitude.";

    return;
  }

  const data = {

    blood_group: document.getElementById("blood_group").value,

    units_needed: Number(document.getElementById("units_needed").value),

    emergency_level: document.getElementById("emergency_level").value,

    hospital_name: document.getElementById("hospital_name").value,

    hospital_latitude: selectedLatitude,

    hospital_longitude: selectedLongitude,

    notes: document.getElementById("notes").value,
  };

  try {
    const response = await fetch(`${API_URL}/api/requests/`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",

        Authorization: `Bearer ${token}`,
      },

      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
      requestMessage.style.color = "red";

      requestMessage.textContent =
        result.message || "Failed to create request.";

      return;
    }

    requestMessage.style.color = "green";

    requestMessage.textContent = "Blood Request Created Successfully.";

    requestForm.reset();

    setTimeout(() => {
      window.location.href = "my-requests.html";
    }, 1500);
  } catch (error) {
    console.error(error);

    requestMessage.style.color = "red";

    requestMessage.textContent = "Unable to connect to backend.";
  }
});
