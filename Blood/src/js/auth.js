const API_URL = "http://127.0.0.1:5000/api";

const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");

// =============================
// USER TYPE TOGGLE BUTTONS
// =============================
if (loginForm) {
  document.querySelectorAll('.type-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      loginForm.dataset.userType = this.dataset.type;
    });
  });
}

// =============================
// LOGIN SUBMISSION HANDLER
// =============================
if (loginForm) {
  loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const selectedType = loginForm.dataset.userType || "donor";

    loginMessage.style.color = "var(--primary-red)";
    loginMessage.textContent = "Logging in...";

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      const result = await response.json();

      console.log("LOGIN RESPONSE:", result);

      if (response.ok) {
        // Save JWT token
        localStorage.setItem("token", result.token);

        // Save logged-in user
        localStorage.setItem("user", JSON.stringify(result.user));
        localStorage.setItem("role", result.user.role);

        const realRole = result.user.role.toLowerCase();
        
        // Redirect logic based on real registered role
        let targetPage = "dashboard.html";
        if (realRole === "hospital") {
          targetPage = "hospital-dashboard.html";
        } else if (realRole === "donor") {
          targetPage = "donor-dashboard.html";
        } else if (realRole === "patient") {
          targetPage = "patient-dashboard.html";
        } else if (realRole === "admin") {
          targetPage = "admin-dashboard.html";
        }

        // Notify user if their selected button differs from registered role
        if (selectedType !== realRole) {
          loginMessage.style.color = "orange";
          loginMessage.innerHTML = `Login successful. Accessing dashboard for your registered role: <strong style="text-transform: capitalize;">${realRole}</strong>. <a href="${targetPage}" style="color: green; font-weight: bold; text-decoration: underline;">Redirecting...</a>`;
        } else {
          loginMessage.style.color = "green";
          loginMessage.innerHTML = `Login successful. <a href="${targetPage}" style="color: green; font-weight: bold; text-decoration: underline;">Click here if not redirected</a>`;
        }

        setTimeout(() => {
          window.location.href = targetPage;
        }, 1500);

      } else {
        if (result.message === "Please verify your email before logging in.") {
          loginMessage.innerHTML = `Please verify your email before logging in.<br><a href="register.html?email=${encodeURIComponent(email)}" style="color: #d9534f; font-weight: bold; text-decoration: underline; display: inline-block; margin-top: 10px;">Verify Now</a>`;
        } else {
          loginMessage.textContent = result.message || `Login failed (${response.status})`;
        }
      }
    } catch (error) {
      console.error("Login Error:", error);
      loginMessage.textContent = "Unable to connect to backend.";
    }
  });
}