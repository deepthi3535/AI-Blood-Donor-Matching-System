const API = "http://127.0.0.1:5000";

document.getElementById("otpForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = localStorage.getItem("reset_email");

  const otp = document.getElementById("otp").value;

  const response = await fetch(`${API}/api/auth/verify-otp`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({
      email,

      otp,
    }),
  });

  const data = await response.json();

  alert(data.message);

  if (response.ok) {
    window.location.href = "reset-password.html";
  }
});
