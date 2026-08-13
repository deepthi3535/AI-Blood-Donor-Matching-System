const API_URL = "http://127.0.0.1:5000";

const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");

loginForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  loginMessage.textContent = "Logging in...";

  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });

    // Convert backend response to JSON
    const result = await response.json();

    console.log("LOGIN RESPONSE:", result);

    if (response.ok) {
      // Save JWT token
      localStorage.setItem("token", result.token);

      // Save logged-in user
      localStorage.setItem("user", JSON.stringify(result.user));
      localStorage.setItem("role", result.user.role);

      const role = result.user.role;
      const targetPage = role === "HOSPITAL" ? "hospital-dashboard.html" : 
                         role === "DONOR" ? "donor-dashboard.html" : 
                         role === "PATIENT" ? "patient-dashboard.html" : 
                         "admin-dashboard.html";

      loginMessage.innerHTML = `Login successful. <a href="${targetPage}" style="color: green; font-weight: bold; text-decoration: underline;">Click here to go to dashboard</a>`;

      // Redirect based on user role
      window.location.href = targetPage;
    } else {
      if (result.message === "Please verify your email before logging in.") {
        loginMessage.innerHTML = `Please verify your email before logging in.<br><a href="register.html?email=${encodeURIComponent(email)}" style="color: #d9534f; font-weight: bold; text-decoration: underline; display: inline-block; margin-top: 10px;">Verify Now</a>`;
      } else {
        loginMessage.textContent =
          result.message || `Login failed (${response.status})`;
      }
    }
  } catch (error) {
    console.error("Login Error:", error);

    loginMessage.textContent = "Unable to connect to backend.";
  }
});