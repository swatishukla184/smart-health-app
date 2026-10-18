/**
 * Smart Health - Gemini AI Forecasting UI Controller
 */

async function checkAIStatus() {
  const pillText = document.getElementById("ai-mode-text");
  if (!pillText) return;

  try {
    const status = await apiFetch("/api/ai/status");
    pillText.textContent = status.active_mode;
    if (status.gemini_api_configured) {
      pillText.parentElement.style.backgroundColor = "var(--color-purple-bg)";
      pillText.parentElement.style.color = "var(--color-purple)";
    } else {
      pillText.parentElement.style.backgroundColor = "#e0f2fe";
      pillText.parentElement.style.color = "#0369a1";
    }
  } catch (err) {
    pillText.textContent = "Offline AI Model";
  }
}
window.checkAIStatus = checkAIStatus;

document.addEventListener("DOMContentLoaded", () => {
  const btnForecastMeds = document.getElementById("btn-forecast-medicines");
  const btnForecastFootfall = document.getElementById("btn-forecast-footfall");
  const loadingContainer = document.getElementById("ai-loading");
  const resultsContainer = document.getElementById("ai-results-container");

  // 1. Forecast Medicine Demand
  btnForecastMeds?.addEventListener("click", async () => {
    loadingContainer.style.display = "block";
    resultsContainer.innerHTML = "";
    announce("Generating medicine demand forecast...");

    try {
      const data = await apiFetch("/api/ai/forecast/medicines", { method: "POST" });
      renderMedicineForecast(data);
      showToast("Medicine demand forecast generated successfully!", "success");
    } catch (err) {
      showToast("Forecast generation failed: " + err.message, "error");
      resultsContainer.innerHTML = `<div class="content-box"><p class="text-danger">Error: ${err.message}</p></div>`;
    } finally {
      loadingContainer.style.display = "none";
    }
  });

  // 2. Forecast Patient Footfall
  btnForecastFootfall?.addEventListener("click", async () => {
    loadingContainer.style.display = "block";
    resultsContainer.innerHTML = "";
    announce("Generating patient footfall surge prediction...");

    try {
      const data = await apiFetch("/api/ai/forecast/footfall", { method: "POST" });
      renderFootfallForecast(data);
      showToast("Patient footfall surge forecast generated!", "success");
    } catch (err) {
      showToast("Footfall forecast failed: " + err.message, "error");
      resultsContainer.innerHTML = `<div class="content-box"><p class="text-danger">Error: ${err.message}</p></div>`;
    } finally {
      loadingContainer.style.display = "none";
    }
  });

  function renderMedicineForecast(data) {
    const isGemini = data.engine_source === "gemini_api";
    const badgeLabel = isGemini ? "Google Gemini 1.5 Flash" : "Statistical Heuristic Engine";

    let html = `
      <div class="content-box" style="margin-bottom: 20px;">
        <div class="box-header">
          <div>
            <h3>7-Day Medicine Demand Forecast & Stockout Risk</h3>
            <p class="text-muted">${escapeHtml(data.summary)}</p>
          </div>
          <span class="stat-badge ${isGemini ? 'badge-neutral' : 'badge-neutral'}" style="background:var(--color-purple-bg); color:var(--color-purple);">
            ✨ ${badgeLabel}
          </span>
        </div>

        <div class="table-container" style="margin-bottom: 20px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Current Stock</th>
                <th>Projected 7-Day Demand</th>
                <th>Days to Exhaustion</th>
                <th>Risk Horizon</th>
                <th>Suggested Order Qty</th>
                <th>Epidemiological Rationale</th>
              </tr>
            </thead>
            <tbody>
    `;

    (data.medicine_forecasts || []).forEach(item => {
      let riskBadge = `<span class="stat-badge badge-success">LOW</span>`;
      if (item.risk_level === "CRITICAL") {
        riskBadge = `<span class="stat-badge badge-danger">CRITICAL</span>`;
      } else if (item.risk_level === "MODERATE") {
        riskBadge = `<span class="stat-badge badge-warning">MODERATE</span>`;
      }

      html += `
        <tr>
          <td><strong>${escapeHtml(item.medicine_name)}</strong></td>
          <td>${item.current_stock}</td>
          <td><strong>${item.projected_7day_demand}</strong></td>
          <td><span class="${item.days_until_stockout <= 3 ? 'text-danger font-bold' : ''}">${item.days_until_stockout} days</span></td>
          <td>${riskBadge}</td>
          <td><strong class="text-primary">${item.suggested_reorder_qty > 0 ? item.suggested_reorder_qty : 'None'}</strong></td>
          <td class="text-muted" style="max-width: 280px; font-size: 0.82rem;">${escapeHtml(item.rationale)}</td>
        </tr>
      `;
    });

    html += `
            </tbody>
          </table>
        </div>

        <div style="background: var(--color-bg); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
          <h4 style="font-size: 0.95rem; font-weight: 800; margin-bottom: 8px;">Recommended Clinical Actions for MOIC:</h4>
          <ul style="padding-left: 20px; font-size: 0.88rem; display: flex; flex-direction: column; gap: 4px;">
            ${(data.recommendations || []).map(r => `<li>${escapeHtml(r)}</li>`).join("")}
          </ul>
        </div>
      </div>
    `;

    resultsContainer.innerHTML = html;
  }

  function renderFootfallForecast(data) {
    const isGemini = data.engine_source === "gemini_api";
    const badgeLabel = isGemini ? "Google Gemini 1.5 Flash" : "Statistical Heuristic Engine";

    let html = `
      <div class="content-box" style="margin-bottom: 20px;">
        <div class="box-header">
          <div>
            <h3>72-Hour Patient Footfall Surge & Bed Congestion Forecast</h3>
            <p class="text-muted">${escapeHtml(data.summary)}</p>
          </div>
          <span class="stat-badge" style="background:var(--color-purple-bg); color:var(--color-purple);">
            ✨ ${badgeLabel}
          </span>
        </div>

        <div class="stats-grid" style="margin-bottom: 20px;">
    `;

    (data.footfall_forecasts || []).forEach(f => {
      html += `
        <div class="stat-card" style="border-left: 4px solid var(--color-primary);">
          <div class="stat-card-header">
            <span class="stat-title">${escapeHtml(f.day_or_window)}</span>
            <span class="stat-badge badge-neutral">${escapeHtml(f.peak_hours)}</span>
          </div>
          <div class="stat-main">
            <span class="stat-number text-primary">${f.predicted_patient_count}</span>
            <span class="stat-unit">expected patients</span>
          </div>
          <div style="font-size: 0.85rem; margin-bottom: 8px;">
            <div><strong>Critical Bottleneck:</strong> ${escapeHtml(f.critical_department)}</div>
            <div><strong>Recommended Medical Officers:</strong> ${f.recommended_staff} on duty</div>
          </div>
        </div>
      `;
    });

    html += `
        </div>

        <div style="background: var(--color-bg); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
          <h4 style="font-size: 0.95rem; font-weight: 800; margin-bottom: 8px;">Surge Preparedness Directives:</h4>
          <ul style="padding-left: 20px; font-size: 0.88rem; display: flex; flex-direction: column; gap: 4px;">
            ${(data.recommendations || []).map(r => `<li>${escapeHtml(r)}</li>`).join("")}
          </ul>
        </div>
      </div>
    `;

    resultsContainer.innerHTML = html;
  }
});
