// Form validation and password strength utility functions

function checkPasswordStrength(password) {
    if (!password) return "";
    if (password.length < 6) return "Weak";
    if (password.length < 10) return "Medium";
    return "Strong";
}

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
    return /^[6-9]\d{9}$/.test(phone);
}

function showNotification(message, type = "info") {
    // Check if container already exists
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.style.position = "fixed";
        container.style.top = "20px";
        container.style.right = "20px";
        container.style.zIndex = "99999";
        document.body.appendChild(container);
    }
    
    const toast = document.createElement("div");
    toast.className = `notification notification-${type}`;
    toast.style.margin = "10px 0";
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

window.checkPasswordStrength = checkPasswordStrength;
window.validateEmail = validateEmail;
window.validatePhone = validatePhone;
window.showNotification = showNotification;
