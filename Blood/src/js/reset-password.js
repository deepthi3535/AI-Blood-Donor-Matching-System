const API_URL = "http://127.0.0.1:5000/api";

document.getElementById("resetForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const password = document.getElementById("password").value;

  const confirm = document.getElementById("confirm").value;

  if (password !== confirm) {
    alert("Passwords do not match");

    return;
  }

  const email = localStorage.getItem("reset_email");

  const response = await fetch(`${API_URL}/auth/reset-password`, {
    method: "PUT",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({
      email,

      password,
    }),
  });

  const data = await response.json();

  alert(data.message);

  if (response.ok) {
    localStorage.removeItem("reset_email");

    window.location.href = "login.html";
  }
});