const API_URL = "http://127.0.0.1:5000/api";

const token = localStorage.getItem("token");

const notificationsContainer = document.getElementById(
  "notificationsContainer",
);

// =======================================
// LOAD NOTIFICATIONS
// =======================================

async function loadNotifications() {
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/notifications/`,

      {
        method: "GET",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const data = await response.json();

    if (!response.ok) {
      notificationsContainer.innerHTML = `
                <p class="error">
                    ${data.message || "Failed to load notifications"}
                </p>
            `;

      return;
    }

    if (data.length === 0) {
      notificationsContainer.innerHTML = `
                <p class="empty">
                    No notifications found.
                </p>
            `;

      return;
    }

    notificationsContainer.innerHTML = "";

    data.forEach((notification) => {
      const card = document.createElement("div");

      card.className = notification.is_read
        ? "notification-card read"
        : "notification-card unread";

      let icon = "🔔";

switch (notification.type || notification.notification_type) {
  case "SUCCESS":
    icon = "✅";
    break;

  case "WARNING":
    icon = "⚠️";
    break;

  case "ERROR":
    icon = "❌";
    break;

  case "INFO":
    icon = "ℹ️";
    break;

  default:
    icon = "🔔";
}

      card.innerHTML = `

                <div class="notification-content">

                    <h3>
                        ${icon} ${notification.title || notification.notification_type}
                    </h3>

                    <p>
                        ${notification.message}
                    </p>

                    ${
                      notification.related_request_id
                        ? `
                        <button
                            class="view-request-btn"
                            onclick="openRequest(${notification.related_request_id})"
                        >
                            🩸 View Request
                        </button>
                        `
                        : ""
                    }

                    <small>
                        ${notification.created_at || ""}
                    </small>

                </div>

                ${
                  !notification.is_read
                    ? `
                    <button
                        class="mark-read-btn"
                        onclick="markAsRead(${notification.notification_id})"
                    >
                        ✓ Mark as Read
                    </button>
                    `
                    : `
                    <span class="read-label">
                        ✓ Read
                    </span>
                    `
                }

            `;

      notificationsContainer.appendChild(card);
    });
  } catch (error) {
    console.error(error);

    notificationsContainer.innerHTML = `
            <p class="error">
                Unable to connect to backend.
            </p>
        `;
  }
}

// =======================================
// MARK AS READ
// =======================================

async function markAsRead(notificationId) {
  try {
    const response = await fetch(
      `${API_URL}/notifications/${notificationId}/read`,

      {
        method: "PATCH",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
if (response.status === 401) {
  localStorage.clear();
  window.location.href = "login.html";
  return;
}
    const data = await response.json();

    if (response.ok) {
      loadNotifications();
    } else {
      alert(data.message);
    }
  } catch (error) {
    console.error(error);
  }
}

// =======================================
// OPEN REQUEST
// =======================================

function openRequest(requestId) {
  localStorage.setItem("selected_request_id", requestId);
  const role = localStorage.getItem("role");

  if (role === "DONOR") {
    window.location.href = "donor-dashboard.html";
  } else if (role === "HOSPITAL") {
    window.location.href = "hospital-dashboard.html";
  } else {
    window.location.href = "my-requests.html";
  }
}

// =======================================
// GO BACK
// =======================================
function goBack() {
  const role = localStorage.getItem("role");

  if (role === "DONOR") {
    window.location.href = "donor-dashboard.html";
  } else if (role === "PATIENT") {
    window.location.href = "patient-dashboard.html";
  } else if (role === "ADMIN") {
    window.location.href = "admin-dashboard.html";
  } else {
    window.location.href = "login.html";
  }
}


// =======================================
// INITIAL LOAD
// =======================================

loadNotifications();

// Auto Refresh Every 10 Seconds

setInterval(
  loadNotifications,

  5000,
);
