const API_URL = "http://127.0.0.1:5000/api";

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");

    // Protect Dashboard: Ensure user is logged in as a HOSPITAL
    if (!token || role !== "HOSPITAL") {
        window.location.href = "login.html";
        return;
    }

    // Load Data
    loadHospitalProfile();
    loadHospitalInventory();
    loadTransfers();

    // Setup Form Handler
    const adjustForm = document.getElementById("adjustForm");
    adjustForm.addEventListener("submit", handleInventoryAdjustment);

    // Setup Logout
    const logoutBtn = document.getElementById("logoutBtn");
    logoutBtn.addEventListener("click", () => {
        localStorage.clear();
        window.location.href = "login.html";
    });
});

async function loadHospitalProfile() {
    const token = localStorage.getItem("token");
    const hospitalInfoContainer = document.getElementById("hospitalInfo");

    try {
        const response = await fetch(`${API_URL}/hospitals/profile`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error("Failed to load hospital profile.");
        }

        const data = await response.json();
        const hospital = data.hospital;

        hospitalInfoContainer.innerHTML = `
            <div class="info-item"><strong>Name:</strong> ${hospital.hospital_name}</div>
            <div class="info-item"><strong>Email:</strong> ${hospital.email || "N/A"}</div>
            <div class="info-item"><strong>Phone:</strong> ${hospital.phone || "N/A"}</div>
            <div class="info-item"><strong>Location:</strong> ${hospital.city || "N/A"}, ${hospital.state || "N/A"}</div>
            <div class="info-item"><strong>Coordinates:</strong> ${hospital.latitude.toFixed(6)}, ${hospital.longitude.toFixed(6)}</div>
            <div class="info-item"><strong>Status:</strong> ${hospital.is_active ? "Active" : "Inactive"}</div>
        `;
    } catch (error) {
        console.error(error);
        hospitalInfoContainer.innerHTML = `<div class="info-item" style="color: red;">Error loading profile.</div>`;
    }
}

async function loadHospitalInventory() {
    const token = localStorage.getItem("token");
    const inventoryContainer = document.getElementById("inventoryContainer");
    const lastUpdatedSpan = document.getElementById("lastUpdated");

    try {
        const response = await fetch(`${API_URL}/hospitals/inventory`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error("Failed to load inventory.");
        }

        const data = await response.json();
        const inventory = data.inventory;

        inventoryContainer.innerHTML = "";

        // Low stock threshold constant: <= 2 is low
        const LOW_STOCK_THRESHOLD = 2;

        Object.keys(inventory).forEach(bg => {
            const units = inventory[bg];
            let statusText = "SUFFICIENT";
            let statusClass = "status-sufficient";

            if (units === 0) {
                statusText = "OUT OF STOCK";
                statusClass = "status-empty";
            } else if (units <= LOW_STOCK_THRESHOLD) {
                statusText = "LOW STOCK";
                statusClass = "status-low";
            }

            const card = document.createElement("div");
            card.className = "inventory-card";
            card.innerHTML = `
                <div class="blood-type">${bg}</div>
                <div class="stock-units">${units} units</div>
                <span class="stock-status ${statusClass}">${statusText}</span>
            `;
            inventoryContainer.appendChild(card);
        });

        // Set last updated time based on first item if available
        if (data.items && data.items.length > 0) {
            lastUpdatedSpan.textContent = `Last updated: ${data.items[0].last_updated}`;
        } else {
            lastUpdatedSpan.textContent = `Last updated: Just now`;
        }

    } catch (error) {
        console.error(error);
        inventoryContainer.innerHTML = `<p style="color: red; text-align: center;">Error loading inventory list.</p>`;
    }
}

async function handleInventoryAdjustment(event) {
    event.preventDefault();

    const token = localStorage.getItem("token");
    const formMessage = document.getElementById("formMessage");
    const bloodGroup = document.getElementById("bloodGroup").value;
    const units = parseInt(document.getElementById("units").value);
    const operation = document.getElementById("operation").value;

    formMessage.textContent = "";

    try {
        const response = await fetch(`${API_URL}/hospitals/inventory/adjust`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                blood_group: bloodGroup,
                units: units,
                operation: operation
            })
        });

        const result = await response.json();

        if (!response.ok) {
            formMessage.textContent = result.message || "Failed to update inventory.";
            formMessage.style.color = "red";
            return;
        }

        formMessage.textContent = result.message;
        formMessage.style.color = "green";

        // Reset form inputs except operation dropdown
        document.getElementById("bloodGroup").selectedIndex = 0;
        document.getElementById("units").value = "";

        // Reload inventory cards
        loadHospitalInventory();

    } catch (error) {
        console.error(error);
        formMessage.textContent = "Error updating inventory stock levels.";
        formMessage.style.color = "red";
    }
}

async function loadTransfers() {
    const token = localStorage.getItem("token");
    const incomingBody = document.getElementById("incomingTransfersBody");
    const outgoingBody = document.getElementById("outgoingTransfersBody");

    // Load Incoming
    try {
        const response = await fetch(`${API_URL}/hospitals/transfers/incoming`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await response.json();
        if (response.ok && result.transfers.length > 0) {
            incomingBody.innerHTML = result.transfers.map(t => `
                <tr>
                    <td><strong>${t.destination_hospital_name}</strong></td>
                    <td><span class="blood-type" style="font-size: 16px; margin: 0;">${t.blood_group}</span></td>
                    <td><strong>${t.units_requested}</strong></td>
                    <td>${t.distance_km} km</td>
                    <td>${t.created_at}</td>
                    <td>
                        ${t.status === 'PENDING' ? `
                            <button onclick="approveTransfer(${t.transfer_id})" class="action-btn btn-approve">Approve</button>
                            <button onclick="rejectTransfer(${t.transfer_id})" class="action-btn btn-reject">Reject</button>
                        ` : `
                            <span class="badge-status badge-${t.status.toLowerCase()}">${t.status}</span>
                        `}
                    </td>
                </tr>
            `).join("");
        } else {
            incomingBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #777;">No incoming transfer requests.</td></tr>`;
        }
    } catch (err) {
        console.error(err);
        incomingBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">Error loading incoming transfers.</td></tr>`;
    }

    // Load Outgoing
    try {
        const response = await fetch(`${API_URL}/hospitals/transfers/outgoing`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await response.json();
        if (response.ok && result.transfers.length > 0) {
            outgoingBody.innerHTML = result.transfers.map(t => `
                <tr>
                    <td><strong>${t.source_hospital_name}</strong></td>
                    <td><span class="blood-type" style="font-size: 16px; margin: 0;">${t.blood_group}</span></td>
                    <td><strong>${t.units_requested}</strong></td>
                    <td>${t.distance_km} km</td>
                    <td><span class="badge-status badge-${t.status.toLowerCase()}">${t.status}</span></td>
                    <td>${t.created_at}</td>
                </tr>
            `).join("");
        } else {
            outgoingBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #777;">No outgoing transfer requests.</td></tr>`;
        }
    } catch (err) {
        console.error(err);
        outgoingBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">Error loading outgoing transfers.</td></tr>`;
    }
}

async function approveTransfer(transferId) {
    const token = localStorage.getItem("token");
    if (!confirm("Are you sure you want to approve this transfer? Inventory will be deducted immediately.")) return;

    try {
        const response = await fetch(`${API_URL}/hospitals/transfers/${transferId}/approve`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await response.json();
        alert(result.message);
        if (response.ok) {
            loadHospitalInventory();
            loadTransfers();
        }
    } catch (err) {
        console.error(err);
        alert("Error approving transfer request.");
    }
}

async function rejectTransfer(transferId) {
    const token = localStorage.getItem("token");
    if (!confirm("Are you sure you want to reject this transfer request?")) return;

    try {
        const response = await fetch(`${API_URL}/hospitals/transfers/${transferId}/reject`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await response.json();
        alert(result.message);
        if (response.ok) {
            loadTransfers();
        }
    } catch (err) {
        console.error(err);
        alert("Error rejecting transfer request.");
    }
}

window.approveTransfer = approveTransfer;
window.rejectTransfer = rejectTransfer;
