document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("gm-open");
  const closeBtn = document.getElementById("gm-close");
  const panel = document.getElementById("genre-panel");
  const overlay = document.getElementById("genre-overlay");

  if (!openBtn || !panel || !overlay) return;

  const openMenu = () => {
    panel.classList.add("active");
    overlay.classList.add("active");
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
  };

  const closeMenu = () => {
    panel.classList.remove("active");
    overlay.classList.remove("active");
    document.documentElement.style.overflow = "";
    document.body.style.overflow = "";
  };

  openBtn.addEventListener("click", openMenu);
  overlay.addEventListener("click", closeMenu);

  if (closeBtn) {
    closeBtn.addEventListener("click", closeMenu);
  }
});
