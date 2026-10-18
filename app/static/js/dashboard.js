/**
 * Smart Health - Live Dashboard & Views Controller
 */

let allMedicines = [];
let allWards = [];
let allDoctors = [];

// ================= TAB NAVIGATION =================
function setupTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");

      // Reset all tabs
      tabs.forEach(t => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".tab-panel").forEach(p => {
        p.classList.remove("active");
        p.hidden = true;
      });

      // Activate selected
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add("active");
        targetPanel.hidden = false;
      }

      // Load tab-specific data if needed
      if (targetId === "medicines-view") loadMedicines();
      if (targetId === "beds-view") loadWards();
      if (targetId === "doctors-view") loadDoctors();
      if (targetId === "ai-view" && window.checkAIStatus) window.checkAIStatus();
    });
  });

  // Quick navigation links
  document.getElementById("link-view-all-beds")?.addEventListener("click", () => {
    document.getElementById("tab-beds")?.click();
  });
  document.getElementById("link-view-all-docs")?.addEventListener("click", () => {
    document.getElementById("tab-doctors")?.click();
  });
}

// ================= ROLE BASED UI RESTRICTIONS =================
function applyRoleVisibility(role) {
  const btnAddMed = document.getElementById("btn-add-medicine-modal");
  const btnQuickStock = document.getElementById("btn-quick-stock");
  const btnQuickBeds = document.getElementById("btn-quick-beds");
  const btnQuickAtt = document.getElementById("btn-quick-attendance");
  const btnAddDoc = document.getElementById("btn-add-doctor-modal");
  const btnSimulateSurge = document.getElementById("btn-simulate-surge");
  const btnResetBaseline = document.getElementById("btn-reset-baseline");
  const btnExportIndent = document.getElementById("btn-export-indent");

  if (role === "pharmacist") {
    if (btnAddMed) btnAddMed.style.display = "inline-flex";
    if (btnQuickStock) btnQuickStock.style.display = "inline-flex";
    if (btnExportIndent) btnExportIndent.style.display = "inline-flex";
    if (btnQuickBeds) btnQuickBeds.style.display = "none";
    if (btnQuickAtt) btnQuickAtt.style.display = "none";
    if (btnAddDoc) btnAddDoc.style.display = "none";
    if (btnSimulateSurge) btnSimulateSurge.style.display = "none";
    if (btnResetBaseline) btnResetBaseline.style.display = "none";
  } else if (role === "doctor") {
    if (btnAddMed) btnAddMed.style.display = "none";
    if (btnQuickStock) btnQuickStock.style.display = "none";
    if (btnExportIndent) btnExportIndent.style.display = "none";
    if (btnQuickBeds) btnQuickBeds.style.display = "inline-flex";
    if (btnQuickAtt) btnQuickAtt.style.display = "inline-flex";
    if (btnAddDoc) btnAddDoc.style.display = "none";
    if (btnSimulateSurge) btnSimulateSurge.style.display = "none";
    if (btnResetBaseline) btnResetBaseline.style.display = "none";
  } else { // Admin (MOIC)
    if (btnAddMed) btnAddMed.style.display = "inline-flex";
    if (btnQuickStock) btnQuickStock.style.display = "inline-flex";
    if (btnExportIndent) btnExportIndent.style.display = "inline-flex";
    if (btnQuickBeds) btnQuickBeds.style.display = "inline-flex";
    if (btnQuickAtt) btnQuickAtt.style.display = "inline-flex";
    if (btnAddDoc) btnAddDoc.style.display = "inline-flex";
    if (btnSimulateSurge) btnSimulateSurge.style.display = "inline-flex";
    if (btnResetBaseline) btnResetBaseline.style.display = "inline-flex";
  }
}
window.applyRoleVisibility = applyRoleVisibility;

// ================= LOAD DASHBOARD METRICS & ALERTS =================
async function loadDashboardStats() {
  try {
    const stats = await apiFetch("/api/dashboard/stats");

    // Live clock update
    const clockEl = document.getElementById("live-clock");
    if (clockEl) clockEl.textContent = stats.current_time;

    // Bed Stats Card
    document.getElementById("stat-free-beds").textContent = stats.available_beds;
    document.getElementById("stat-bed-badge").textContent = `${stats.bed_occupancy_percent}% Occupied`;
    const bedFill = document.getElementById("bed-progress-fill");
    const bedBar = document.getElementById("bed-progress-bar");
    if (bedFill && bedBar) {
      bedFill.style.width = `${Math.min(stats.bed_occupancy_percent, 100)}%`;
      bedBar.setAttribute("aria-valuenow", stats.bed_occupancy_percent);
      if (stats.bed_occupancy_percent >= 90) {
        bedFill.style.backgroundColor = "var(--color-danger)";
        document.getElementById("stat-bed-badge").className = "stat-badge badge-danger";
      } else if (stats.bed_occupancy_percent >= 75) {
        bedFill.style.backgroundColor = "var(--color-warning)";
        document.getElementById("stat-bed-badge").className = "stat-badge badge-warning";
      } else {
        bedFill.style.backgroundColor = "var(--color-success)";
        document.getElementById("stat-bed-badge").className = "stat-badge badge-success";
      }
    }
    document.getElementById("stat-beds-breakdown").textContent =
      `Total: ${stats.total_beds} | Occupied: ${stats.occupied_beds} | Available: ${stats.available_beds}`;

    // Medicine Stats Card
    document.getElementById("stat-total-meds").textContent = stats.total_medicines;
    document.getElementById("stat-stockout-count").textContent = `${stats.out_of_stock_medicines} Out of Stock`;
    document.getElementById("stat-lowstock-count").textContent = `${stats.low_stock_medicines} Low Stock`;
    const stockBadge = document.getElementById("stat-stock-badge");
    const totalStockAlerts = stats.out_of_stock_medicines + stats.low_stock_medicines;
    if (stockBadge) {
      stockBadge.textContent = `${totalStockAlerts} Stock Alerts`;
      stockBadge.className = totalStockAlerts > 0 ? "stat-badge badge-danger" : "stat-badge badge-success";
    }

    // Doctor Attendance Card
    document.getElementById("stat-onduty-doctors").textContent = stats.doctors_on_duty;
    document.getElementById("stat-total-doctors").textContent = `/ ${stats.total_doctors} doctors`;
    const docBadge = document.getElementById("stat-doc-badge");
    if (docBadge) {
      if (stats.doctors_on_duty === 0) {
        docBadge.textContent = "Urgent";
        docBadge.className = "stat-badge badge-danger";
      } else {
        docBadge.textContent = "Normal";
        docBadge.className = "stat-badge badge-success";
      }
    }

    // Footfall Card
    document.getElementById("stat-today-footfall").textContent = stats.today_footfall;

    // Render Urgent Alerts Banner
    renderAlerts(stats.active_alerts);

  } catch (err) {
    console.error("Failed to load dashboard stats:", err);
  }
}

function renderAlerts(alerts) {
  const container = document.getElementById("alerts-container");
  const countEl = document.getElementById("alert-count-number");
  const section = document.getElementById("alerts-section");
  if (!container || !countEl) return;

  countEl.textContent = alerts.length;
  if (alerts.length === 0) {
    container.innerHTML = `<div class="alert-pill" style="background:#ecfdf5; color:#065f46; border-color:#a7f3d0;">
      ✓ All PHC/CHC systems normal: no stock-out or critical capacity alerts active.
    </div>`;
    return;
  }

  container.innerHTML = alerts.slice(0, 4).map(a => `
    <div class="alert-pill ${a.severity.toLowerCase()}" role="listitem">
      <span><strong>${escapeHtml(a.title)}:</strong> ${escapeHtml(a.message)}</span>
      <span class="stat-badge ${a.severity === 'DANGER' ? 'badge-danger' : 'badge-warning'}">${a.category}</span>
    </div>
  `).join("");
}

// ================= LOAD MEDICINES VIEW =================
async function loadMedicines() {
  try {
    allMedicines = await apiFetch("/api/medicines");
    renderMedicinesTable(allMedicines);
  } catch (err) {
    showToast("Failed to fetch medicines: " + err.message, "error");
  }
}

function renderMedicinesTable(items) {
  const tbody = document.getElementById("medicines-tbody");
  if (!tbody) return;

  const role = getActiveRole();
  const canModify = role === "admin" || role === "pharmacist";
  const canDelete = role === "admin";

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-muted" style="text-align:center; padding: 24px;">No matching medicines found.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(m => {
    let statusBadge = `<span class="stat-badge badge-success">IN STOCK</span>`;
    if (m.status === "OUT_OF_STOCK") {
      statusBadge = `<span class="stat-badge badge-danger">OUT OF STOCK</span>`;
    } else if (m.status === "LOW_STOCK") {
      statusBadge = `<span class="stat-badge badge-warning">LOW STOCK</span>`;
    } else if (m.status === "EXPIRED") {
      statusBadge = `<span class="stat-badge badge-danger">EXPIRED</span>`;
    }

    return `
      <tr>
        <td>
          <strong>${escapeHtml(m.name)}</strong>
          <div class="stat-footer-text" style="border:none; padding:0; margin:0;">${escapeHtml(m.dosage_form)}</div>
        </td>
        <td>${escapeHtml(m.category)}</td>
        <td>
          <span class="font-bold ${m.current_quantity === 0 ? 'text-danger' : ''}">${m.current_quantity}</span>
          <span class="text-muted">${escapeHtml(m.unit)}</span>
        </td>
        <td>${m.reorder_level} ${escapeHtml(m.unit)}</td>
        <td>${statusBadge}</td>
        <td>
          <div>${escapeHtml(m.batch_number)}</div>
          <small class="text-muted">Exp: ${m.expiry_date}</small>
        </td>
        <td class="text-right">
          ${canModify ? `
            <button class="btn-xs btn-outline btn-adjust-stock" data-id="${m.id}" data-name="${escapeHtml(m.name)}" data-unit="${escapeHtml(m.unit)}" data-qty="${m.current_quantity}">
              Update Stock
            </button>
          ` : `<span class="text-muted">-</span>`}
          ${canDelete ? `
            <button class="btn-xs btn-text text-danger btn-delete-med" data-id="${m.id}" style="margin-left:6px;" aria-label="Delete ${escapeHtml(m.name)}">
              Delete
            </button>
          ` : ``}
        </td>
      </tr>
    `;
  }).join("");

  // Attach button listeners
  document.querySelectorAll(".btn-adjust-stock").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const unit = btn.getAttribute("data-unit");
      const qty = btn.getAttribute("data-qty");
      window.openStockModal(id, name, unit, qty);
    });
  });

  document.querySelectorAll(".btn-delete-med").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      if (confirm(`Are you sure you want to delete medicine record ${id}?`)) {
        try {
          await apiFetch(`/api/medicines/${id}`, { method: "DELETE" });
          showToast("Medicine deleted successfully", "success");
          loadMedicines();
          loadDashboardStats();
        } catch (e) {
          showToast("Delete failed: " + e.message, "error");
        }
      }
    });
  });
}

// Search and filter listeners
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("med-search");
  const filterSelect = document.getElementById("med-filter-status");

  function applyMedFilter() {
    const query = (searchInput?.value || "").toLowerCase().trim();
    const st = filterSelect?.value || "";

    const filtered = allMedicines.filter(m => {
      const matchQuery = !query || m.name.toLowerCase().includes(query) ||
        m.category.toLowerCase().includes(query) || m.batch_number.toLowerCase().includes(query);
      const matchStatus = !st || m.status === st;
      return matchQuery && matchStatus;
    });

    renderMedicinesTable(filtered);
  }

  searchInput?.addEventListener("input", applyMedFilter);
  filterSelect?.addEventListener("change", applyMedFilter);
});

// ================= LOAD WARDS / BEDS =================
async function loadWards() {
  try {
    allWards = await apiFetch("/api/beds");
    renderDashboardWards(allWards);
    renderFullWards(allWards);
    populateWardDropdown(allWards);
  } catch (err) {
    console.error("Failed to load wards:", err);
  }
}

function renderDashboardWards(wards) {
  const container = document.getElementById("dashboard-wards-list");
  if (!container) return;

  container.innerHTML = wards.map(w => {
    const isCritical = w.occupancy_rate >= 90;
    return `
      <div class="ward-item">
        <div class="ward-item-header">
          <span>${escapeHtml(w.ward_name)}</span>
          <span class="stat-badge ${isCritical ? 'badge-danger' : 'badge-neutral'}">${w.occupancy_rate}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${w.occupancy_rate}%; background-color: ${isCritical ? 'var(--color-danger)' : 'var(--color-primary)'}"></div>
        </div>
        <div class="stat-footer-text" style="border:none; padding:0; margin:0;">
          Free: <strong>${w.available_beds}</strong> | Occupied: ${w.occupied_beds} | Cleaning: ${w.cleaning_beds}
        </div>
      </div>
    `;
  }).join("");
}

function renderFullWards(wards) {
  const container = document.getElementById("wards-full-container");
  if (!container) return;

  const role = getActiveRole();
  const canUpdate = role === "admin" || role === "doctor";

  container.innerHTML = wards.map(w => `
    <div class="ward-full-card">
      <div class="ward-item-header">
        <h3>${escapeHtml(w.ward_name)}</h3>
        <span class="stat-badge ${w.occupancy_rate >= 90 ? 'badge-danger' : 'badge-neutral'}">${w.occupancy_rate}% Full</span>
      </div>
      <div class="progress-bar-bg" style="height: 12px; margin: 12px 0;">
        <div class="progress-bar-fill" style="width: ${w.occupancy_rate}%; background-color: ${w.occupancy_rate >= 90 ? 'var(--color-danger)' : 'var(--color-primary)'}"></div>
      </div>
      <div class="stats-grid" style="grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 12px 0;">
        <div style="text-align:center; background: var(--color-bg); padding: 8px; border-radius: var(--radius-sm);">
          <div class="font-bold">${w.total_beds}</div>
          <small class="text-muted">Total</small>
        </div>
        <div style="text-align:center; background: var(--color-bg); padding: 8px; border-radius: var(--radius-sm);">
          <div class="font-bold text-danger">${w.occupied_beds}</div>
          <small class="text-muted">Occupied</small>
        </div>
        <div style="text-align:center; background: var(--color-bg); padding: 8px; border-radius: var(--radius-sm);">
          <div class="font-bold text-success">${w.available_beds}</div>
          <small class="text-muted">Available</small>
        </div>
      </div>
      ${canUpdate ? `
        <button class="btn btn-secondary btn-update-ward" style="width: 100%; margin-top: 10px;" data-id="${w.ward_id}" data-occupied="${w.occupied_beds}" data-cleaning="${w.cleaning_beds}">
          Edit Bed Occupancy
        </button>
      ` : ``}
    </div>
  `).join("");

  document.querySelectorAll(".btn-update-ward").forEach(btn => {
    btn.addEventListener("click", () => {
      const wardId = btn.getAttribute("data-id");
      const occ = btn.getAttribute("data-occupied");
      const clean = btn.getAttribute("data-cleaning");
      window.openBedModal(wardId, occ, clean);
    });
  });
}

function populateWardDropdown(wards) {
  const select = document.getElementById("bed-ward-select");
  if (!select) return;
  select.innerHTML = wards.map(w => `
    <option value="${w.ward_id}" data-total="${w.total_beds}">${escapeHtml(w.ward_name)} (Max: ${w.total_beds})</option>
  `).join("");
}

// ================= LOAD DOCTORS =================
async function loadDoctors() {
  try {
    allDoctors = await apiFetch("/api/doctors");
    renderDashboardDoctors(allDoctors);
    renderFullDoctors(allDoctors);
  } catch (err) {
    console.error("Failed to load doctors:", err);
  }
}

function renderDashboardDoctors(doctors) {
  const container = document.getElementById("dashboard-doctors-list");
  if (!container) return;

  container.innerHTML = doctors.slice(0, 5).map(d => `
    <div class="doctor-row">
      <div>
        <strong>${escapeHtml(d.name)}</strong>
        <div class="text-muted" style="font-size: 0.8rem;">${escapeHtml(d.specialization)} | ${escapeHtml(d.room_number)}</div>
      </div>
      <div>
        <span class="stat-badge ${d.is_present ? 'badge-success' : 'badge-neutral'}">
          ${d.status}
        </span>
      </div>
    </div>
  `).join("");
}

function renderFullDoctors(doctors) {
  const container = document.getElementById("doctors-full-container");
  if (!container) return;

  const role = getActiveRole();
  const canToggle = role === "admin" || role === "doctor";

  container.innerHTML = doctors.map(d => `
    <div class="doctor-card">
      <div>
        <div class="ward-item-header">
          <h3>${escapeHtml(d.name)}</h3>
          <span class="stat-badge ${d.is_present ? 'badge-success' : 'badge-neutral'}">${d.status}</span>
        </div>
        <p class="text-muted font-bold">${escapeHtml(d.specialization)}</p>
        <div style="margin: 12px 0; font-size: 0.88rem;">
          <div><strong>Shift:</strong> ${escapeHtml(d.shift)}</div>
          <div><strong>Station:</strong> ${escapeHtml(d.room_number)}</div>
          <div><strong>Attendance:</strong> ${d.is_present ? 'Checked In' : 'Not Present'}</div>
        </div>
      </div>
      ${canToggle ? `
        <button class="btn ${d.is_present ? 'btn-secondary' : 'btn-primary'} btn-toggle-doc" data-id="${d.doctor_id}" data-present="${d.is_present}">
          ${d.is_present ? 'Mark Check-Out' : 'Check-In to Duty'}
        </button>
      ` : ``}
    </div>
  `).join("");

  document.querySelectorAll(".btn-toggle-doc").forEach(btn => {
    btn.addEventListener("click", async () => {
      const docId = btn.getAttribute("data-id");
      const isPresent = btn.getAttribute("data-present") === "true";
      try {
        await apiFetch(`/api/doctors/${docId}/toggle-attendance`, {
          method: "POST",
          body: JSON.stringify({ is_present: !isPresent })
        });
        showToast("Doctor attendance updated", "success");
        loadDoctors();
        loadDashboardStats();
      } catch (err) {
        showToast("Failed to toggle attendance: " + err.message, "error");
      }
    });
  });
}

// Utility: HTML escape
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ================= 7-DAY FOOTFALL CHART RENDERING =================
async function loadFootfallChart() {
  const container = document.getElementById("footfall-chart-container");
  const summaryBadge = document.getElementById("footfall-trend-summary");
  if (!container) return;

  try {
    const rawFootfall = await apiFetch("/api/footfall?limit=60");
    
    // Group by date
    const dailyTotals = {};
    const deptTotals = {};

    rawFootfall.forEach(entry => {
      const d = entry.date;
      dailyTotals[d] = (dailyTotals[d] || 0) + entry.patient_count;
      deptTotals[entry.department] = (deptTotals[entry.department] || 0) + entry.patient_count;
    });

    const dates = Object.keys(dailyTotals).sort().slice(-7);
    if (dates.length === 0) {
      container.innerHTML = `<p class="text-muted" style="text-align:center; padding:20px;">No historical footfall records available.</p>`;
      return;
    }

    const maxVal = Math.max(...dates.map(d => dailyTotals[d]), 50);
    const chartHeight = 140;
    const chartWidth = 620;
    const barWidth = 44;
    const gap = (chartWidth - 60 - (dates.length * barWidth)) / (dates.length - 1);

    let barsSvg = "";
    dates.forEach((d, idx) => {
      const count = dailyTotals[d];
      const barH = Math.round((count / maxVal) * chartHeight);
      const x = 40 + idx * (barWidth + gap);
      const y = 150 - barH;

      // Format short label (e.g. "Sun 18")
      let dateLabel = d.slice(5);
      try {
        const parsed = new Date(d + "T00:00:00");
        dateLabel = parsed.toLocaleDateString("en-US", { weekday: "short", day: "numeric" });
      } catch (_) {}

      // Color coding (highlight surge > 200)
      const barColor = count >= 200 ? "#b91c1c" : (count >= 160 ? "#d97706" : "#0284c7");

      barsSvg += `
        <g class="chart-group" tabindex="0" role="graphics-symbol" aria-label="${dateLabel}: ${count} patients">
          <title>${dateLabel}: ${count} Total Patients</title>
          <rect class="chart-bar" x="${x}" y="${y}" width="${barWidth}" height="${barH}" rx="4" fill="${barColor}">
            <animate attributeName="height" from="0" to="${barH}" dur="0.4s" fill="freeze" />
            <animate attributeName="y" from="150" to="${y}" dur="0.4s" fill="freeze" />
          </rect>
          <text class="chart-val-label" x="${x + barWidth / 2}" y="${y - 6}">${count}</text>
          <text class="chart-label" x="${x + barWidth / 2}" y="170">${dateLabel}</text>
        </g>
      `;
    });

    container.innerHTML = `
      <svg class="svg-chart" viewBox="0 0 ${chartWidth} 190" aria-label="Interactive 7-day patient footfall graph" role="img">
        <line x1="30" y1="150" x2="${chartWidth - 20}" y2="150" class="chart-axis-line" />
        ${barsSvg}
      </svg>
    `;

    if (summaryBadge) {
      const latestCount = dailyTotals[dates[dates.length - 1]] || 0;
      summaryBadge.textContent = latestCount >= 180 ? "⚠️ Surge Volume Detected" : "Normal Weekly Influx";
      summaryBadge.className = latestCount >= 180 ? "stat-badge badge-warning" : "stat-badge badge-success";
    }

  } catch (err) {
    console.error("Failed to render footfall chart:", err);
  }
}

// Global Refresh
function refreshAllData() {
  loadDashboardStats();
  loadWards();
  loadDoctors();
  loadMedicines();
  loadFootfallChart();
}
window.refreshAllData = refreshAllData;

// Initializer & Demo Action Handlers
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  refreshAllData();

  document.getElementById("refresh-all-btn")?.addEventListener("click", () => {
    refreshAllData();
    showToast("Dashboard data refreshed", "info");
  });

  // Demo Feature: Simulate Monsoon Epidemic Surge
  document.getElementById("btn-simulate-surge")?.addEventListener("click", async () => {
    try {
      announce("Injecting simulated monsoon surge...");
      const resp = await apiFetch("/api/dashboard/simulate-surge", { method: "POST" });
      
      const banner = document.getElementById("alerts-section");
      if (banner) {
        banner.classList.add("surge-pulse");
        setTimeout(() => banner.classList.remove("surge-pulse"), 4500);
      }
      
      showToast(resp.message, "error");
      refreshAllData();
    } catch (err) {
      showToast("Simulation failed: " + err.message, "error");
    }
  });

  // Demo Feature: Reset to Baseline
  document.getElementById("btn-reset-baseline")?.addEventListener("click", async () => {
    try {
      announce("Resetting facility baseline data...");
      const resp = await apiFetch("/api/dashboard/reset-baseline", { method: "POST" });
      showToast(resp.message, "success");
      refreshAllData();
    } catch (err) {
      showToast("Reset failed: " + err.message, "error");
    }
  });

  // Feature: Export District Drug Warehouse Indent (CSV)
  document.getElementById("btn-export-indent")?.addEventListener("click", () => {
    announce("Exporting district drug indent requisition sheet...");
    showToast("Generating official NHM District Drug Indent CSV...", "info");
    window.location.href = "/api/medicines/export/indent";
  });

  // Background Auto-polling every 12 seconds
  setInterval(() => {
    loadDashboardStats();
  }, 12000);
});

