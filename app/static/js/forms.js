/**
 * Smart Health - Accessible Modal & Form Handlers
 */

let lastFocusedElement = null;

// ================= ACCESSIBLE MODAL SYSTEM =================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  lastFocusedElement = document.activeElement;
  modal.removeAttribute("hidden");
  modal.style.display = "flex";

  // Focus first interactive element
  const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusable.length > 0) {
    focusable[0].focus();
  }

  // Trap focus listener
  modal.addEventListener("keydown", trapFocus);
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  modal.setAttribute("hidden", "true");
  modal.style.display = "none";
  modal.removeEventListener("keydown", trapFocus);

  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}

function trapFocus(e) {
  if (e.key === "Escape") {
    closeModal(this.id);
    return;
  }
  if (e.key !== "Tab") return;

  const focusable = this.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  if (e.shiftKey) {
    if (document.activeElement === first) {
      last.focus();
      e.preventDefault();
    }
  } else {
    if (document.activeElement === last) {
      first.focus();
      e.preventDefault();
    }
  }
}

// Global modal triggers
window.openStockModal = function(id, name, unit, qty) {
  document.getElementById("stock-med-id").value = id;
  document.getElementById("stock-med-name").value = name;
  document.getElementById("stock-unit-label").textContent = unit || "units";
  document.getElementById("stock-available-hint").textContent = `Available in stock: ${qty} ${unit || 'units'}`;
  document.getElementById("stock-available-hint").setAttribute("data-max", qty);
  document.getElementById("stock-quantity").value = "";
  openModal("modal-stock");
};

window.openBedModal = function(wardId, occupied, cleaning) {
  const select = document.getElementById("bed-ward-select");
  if (select && wardId) select.value = wardId;
  document.getElementById("bed-occupied-input").value = occupied || 0;
  document.getElementById("bed-cleaning-input").value = cleaning || 0;
  updateBedCapacityDisplay();
  openModal("modal-beds");
};

function updateBedCapacityDisplay() {
  const select = document.getElementById("bed-ward-select");
  const selectedOption = select?.options[select.selectedIndex];
  const total = selectedOption?.getAttribute("data-total") || "-";
  document.getElementById("bed-total-capacity").textContent = total;
}

// ================= FORM SUBMISSIONS =================
document.addEventListener("DOMContentLoaded", () => {
  // Modal Close buttons
  document.getElementById("close-modal-stock")?.addEventListener("click", () => closeModal("modal-stock"));
  document.getElementById("cancel-modal-stock")?.addEventListener("click", () => closeModal("modal-stock"));

  document.getElementById("close-modal-beds")?.addEventListener("click", () => closeModal("modal-beds"));
  document.getElementById("cancel-modal-beds")?.addEventListener("click", () => closeModal("modal-beds"));

  document.getElementById("close-modal-add-med")?.addEventListener("click", () => closeModal("modal-add-med"));
  document.getElementById("cancel-modal-add-med")?.addEventListener("click", () => closeModal("modal-add-med"));

  document.getElementById("close-modal-footfall")?.addEventListener("click", () => closeModal("modal-footfall"));
  document.getElementById("cancel-modal-footfall")?.addEventListener("click", () => closeModal("modal-footfall"));

  // Quick Open Buttons
  document.getElementById("btn-quick-stock")?.addEventListener("click", () => {
    // Open stock modal with first medicine if none selected
    if (window.allMedicines && window.allMedicines.length > 0) {
      const first = window.allMedicines[0];
      window.openStockModal(first.id, first.name, first.unit, first.current_quantity);
    } else {
      document.getElementById("tab-medicines")?.click();
    }
  });

  document.getElementById("btn-quick-beds")?.addEventListener("click", () => {
    window.openBedModal();
  });

  document.getElementById("btn-quick-attendance")?.addEventListener("click", () => {
    document.getElementById("tab-doctors")?.click();
  });

  document.getElementById("btn-add-medicine-modal")?.addEventListener("click", () => {
    openModal("modal-add-med");
  });

  document.getElementById("btn-add-footfall")?.addEventListener("click", () => {
    openModal("modal-footfall");
  });

  document.getElementById("bed-ward-select")?.addEventListener("change", updateBedCapacityDisplay);

  // 1. Stock Update Submission
  const stockForm = document.getElementById("form-stock-update");
  stockForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const medId = document.getElementById("stock-med-id").value;
    const action = document.getElementById("stock-action").value;
    const qty = parseInt(document.getElementById("stock-quantity").value, 10);
    const notes = document.getElementById("stock-notes").value;
    const maxAvailable = parseInt(document.getElementById("stock-available-hint").getAttribute("data-max") || "0", 10);

    if (!qty || qty <= 0) {
      showToast("Please enter a valid positive quantity", "error");
      return;
    }

    if (action === "DEDUCT" && qty > maxAvailable) {
      showToast(`Cannot dispense ${qty} units. Only ${maxAvailable} available in stock.`, "error");
      return;
    }

    try {
      await apiFetch(`/api/medicines/${medId}/stock`, {
        method: "PUT",
        body: JSON.stringify({ action, quantity: qty, notes: notes || null })
      });
      showToast("Medicine stock updated successfully!", "success");
      closeModal("modal-stock");
      window.refreshAllData();
    } catch (err) {
      showToast("Stock update failed: " + err.message, "error");
    }
  });

  // 2. Bed Update Submission
  const bedsForm = document.getElementById("form-beds-update");
  bedsForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const select = document.getElementById("bed-ward-select");
    const wardId = select.value;
    const total = parseInt(select.options[select.selectedIndex]?.getAttribute("data-total") || "0", 10);
    const occupied = parseInt(document.getElementById("bed-occupied-input").value, 10);
    const cleaning = parseInt(document.getElementById("bed-cleaning-input").value, 10);

    if (isNaN(occupied) || isNaN(cleaning) || occupied < 0 || cleaning < 0) {
      showToast("Please enter valid positive numbers for bed counts.", "error");
      return;
    }

    if (occupied + cleaning > total) {
      showToast(`Occupied (${occupied}) + Cleaning (${cleaning}) exceeds total ward capacity (${total})!`, "error");
      return;
    }

    try {
      await apiFetch(`/api/beds/${wardId}`, {
        method: "PUT",
        body: JSON.stringify({ occupied_beds: occupied, cleaning_beds: cleaning })
      });
      showToast("Ward bed allocation saved!", "success");
      closeModal("modal-beds");
      window.refreshAllData();
    } catch (err) {
      showToast("Bed update failed: " + err.message, "error");
    }
  });

  // 3. Add Medicine Submission
  const addMedForm = document.getElementById("form-add-medicine");
  addMedForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("new-med-name").value.trim();
    const category = document.getElementById("new-med-category").value.trim();
    const dosage_form = document.getElementById("new-med-form").value.trim();
    const current_quantity = parseInt(document.getElementById("new-med-quantity").value, 10);
    const unit = document.getElementById("new-med-unit").value.trim();
    const reorder_level = parseInt(document.getElementById("new-med-reorder").value, 10);
    const expiry_date = document.getElementById("new-med-expiry").value;
    const batch_number = document.getElementById("new-med-batch").value.trim() || "BATCH-GEN";

    if (!name || !category || !dosage_form || !unit || !expiry_date) {
      showToast("Please fill in all required fields.", "error");
      return;
    }

    try {
      await apiFetch("/api/medicines", {
        method: "POST",
        body: JSON.stringify({
          name,
          category,
          dosage_form,
          current_quantity,
          unit,
          reorder_level,
          expiry_date,
          batch_number,
        })
      });
      showToast(`Added '${name}' to pharmacy inventory!`, "success");
      closeModal("modal-add-med");
      addMedForm.reset();
      window.refreshAllData();
    } catch (err) {
      showToast("Failed to add medicine: " + err.message, "error");
    }
  });

  // 4. Log Footfall Submission
  const footfallForm = document.getElementById("form-footfall");
  footfallForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const department = document.getElementById("ff-department").value;
    const count = parseInt(document.getElementById("ff-count").value, 10);

    if (!count || count <= 0) {
      showToast("Please enter a valid patient count.", "error");
      return;
    }

    try {
      await apiFetch("/api/footfall", {
        method: "POST",
        body: JSON.stringify({ department, patient_count: count })
      });
      showToast(`Logged ${count} patient arrivals in ${department}`, "success");
      closeModal("modal-footfall");
      window.refreshAllData();
    } catch (err) {
      showToast("Footfall recording failed: " + err.message, "error");
    }
  });
});
