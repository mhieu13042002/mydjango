// Dark / Light mode
(function () {
  const stored = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", stored);
  window.addEventListener("DOMContentLoaded", () => {
    updateThemeIcon(stored);
  });
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const icon = document.getElementById("themeIcon");
  if (icon) icon.className = theme === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
}

// CSRF helper cho AJAX
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}
const CSRF_TOKEN = getCookie("csrftoken");

// Toast helper (Bootstrap 5 Toast)
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const icons = { success: "fa-circle-check text-success", error: "fa-circle-exclamation text-danger", warning: "fa-triangle-exclamation text-warning", info: "fa-circle-info text-info" };
  const el = document.createElement("div");
  el.className = "toast toast-custom align-items-center border-0 mb-2 glass";
  el.setAttribute("role", "alert");
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="fa-solid ${icons[type] || icons.info}"></i> ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(el);
  const toast = new bootstrap.Toast(el, { delay: 4000 });
  toast.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}

// Sidebar mobile toggle
function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("show");
}

// Confirm dialog dùng chung cho các nút xoá
function confirmAction(message) {
  return window.confirm(message);
}
