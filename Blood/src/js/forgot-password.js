const API = "http://127.0.0.1:5000";

document.getElementById("forgotForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value;

  const response = await fetch(`${API}/api/auth/forgot-password`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({ email }),
  });

  const data = await response.json();

  alert(data.message);

  if (response.ok) {
    localStorage.setItem("reset_email", email);

    window.location.href = "verify-otp.html";
  }
});
