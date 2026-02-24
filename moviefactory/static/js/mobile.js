document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("gm-open");
  const closeBtn = document.getElementById("gm-close");
  const overlay = document.getElementById("genre-overlay");
  const panel = document.getElementById("genre-panel");

  if (!openBtn || !closeBtn || !overlay || !panel) return;

  let scrollY = 0;

  const openMenu = () => {
    // ✅ 현재 스크롤 위치 저장
    scrollY = window.scrollY;

    overlay.classList.add("is-open");
    panel.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");

    // ✅ 배경 스크롤 잠금
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
  };

  const closeMenu = () => {
    overlay.classList.remove("is-open");
    panel.classList.remove("is-open");
    overlay.setAttribute("aria-hidden", "true");

    // ✅ 배경 스크롤 복구
    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";

    window.scrollTo(0, scrollY);
  };

  openBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    openMenu();
  });

  closeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    closeMenu();
  });

  overlay.addEventListener("click", (e) => {
    e.preventDefault();
    closeMenu();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
});
