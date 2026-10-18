/**
 * Smart Health - Central API Client & Notification Engine
 */

let currentRole = "admin";

function getActiveRole() {
  const roleSelect = document.getElementById("role-select");
  if (roleSelect) {
    return roleSelect.value;
  }
  return currentRole;
}

function announce(message) {
  const announcer = document.getElementById("live-announcer");
  if (announcer) {
    announcer.textContent = message;
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.setAttribute("role", "alert");
  toast.textContent = message;

  container.appendChild(toast);
  announce(message);

  setTimeout(() => {
    toast.remove();
  }, 4000);
}

async function apiFetch(endpoint, options = {}) {
  const role = getActiveRole();
  const headers = {
    "Content-Type": "application/json",
    "X-User-Role": role,
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(endpoint, { ...options, headers });
    if (!res.ok) {
      let errorDetail = `Request failed (${res.status})`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          if (Array.isArray(errorJson.detail)) {
            errorDetail = errorJson.detail.map(e => e.msg || JSON.stringify(e)).join(", ");
          } else {
            errorDetail = errorJson.detail;
          }
        }
      } catch (_) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// Role select event listener
document.addEventListener("DOMContentLoaded", () => {
  const roleSelect = document.getElementById("role-select");
  const roleBadge = document.getElementById("current-role-badge");

  if (roleSelect && roleBadge) {
    roleSelect.addEventListener("change", (e) => {
      currentRole = e.target.value;
      roleBadge.textContent = currentRole.toUpperCase();
      announce(`Role switched to ${currentRole}`);
      showToast(`Operational role switched to ${currentRole.toUpperCase()}`, "info");
      
      // Update role-sensitive UI
      if (window.applyRoleVisibility) {
        window.applyRoleVisibility(currentRole);
      }
      // Refresh current view data
      if (window.refreshAllData) {
        window.refreshAllData();
      }
    });
  }
});
