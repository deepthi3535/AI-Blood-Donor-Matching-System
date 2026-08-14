const API_URL = "http://127.0.0.1:5000/api";

window.API = {
  api: {
    getToken: () => localStorage.getItem("token")
  },
  auth: {
    logout: () => {
      localStorage.clear();
      window.location.href = "login.html";
    },
    registerPatient: async (data) => {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data, role: "PATIENT" })
      });
      const result = await response.json();
      return { success: response.ok, message: result.message, data: result };
    },
    registerDonor: async (data) => {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data, role: "DONOR" })
      });
      const result = await response.json();
      return { success: response.ok, message: result.message, data: result };
    }
  },
  donor: {
    getProfile: async () => {
      const response = await fetch(`${API_URL}/donors/dashboard`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      const result = await response.json();
      return { success: response.ok, data: { name: result.donor?.full_name, total_donations: result.total_donations, is_available: result.donor?.availability } };
    },
    getGamification: async () => {
      const response = await fetch(`${API_URL}/donors/dashboard`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      const result = await response.json();
      return { success: response.ok, data: { points: result.reward_points, tier: result.donor?.badge || "Bronze" } };
    },
    getHistory: async () => {
      const response = await fetch(`${API_URL}/donors/dashboard`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      const result = await response.json();
      const history = (result.recent_donations || []).map((d, i) => ({
        history_id: d.donation_id || i + 1,
        request_id: d.request_id || "N/A",
        donation_date: d.donation_date,
        status: d.status || "Completed"
      }));
      return { success: response.ok, data: history };
    },
    updateAvailability: async (available) => {
      const response = await fetch(`${API_URL}/donors/availability`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({ availability: available })
      });
      const result = await response.json();
      return { success: response.ok, message: result.message || "Availability updated" };
    }
  },
  patient: {
    getRequests: async () => {
      const response = await fetch(`${API_URL}/patients/dashboard`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      const result = await response.json();
      const requests = (result.recent_activities || []).map((req, i) => ({
        request_id: req.request_id || i + 1,
        blood_group: req.blood_group,
        hospital_name: req.hospital,
        units_needed: 1,
        status: req.status,
        emergency_level: "Urgent",
        request_time: req.request_time
      }));
      return { success: response.ok, data: requests };
    }
  }
};
