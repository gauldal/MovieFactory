document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-explain");
  const box = document.getElementById("explanation-result");

  if (!btn || !box) return;

  const LABEL_OPEN = "See Why";
  const LABEL_CLOSE = "Close";
  const LABEL_LOADING = "Generating explanation…";

  // 초기 상태
  box.style.display = "none";
  box.dataset.loaded = "false";
  box.dataset.open = "false";
  btn.textContent = LABEL_OPEN;
  btn.setAttribute("aria-expanded", "false");

  function openBox() {
    box.style.display = "block";
    box.dataset.open = "true";
    btn.textContent = LABEL_CLOSE;
    btn.setAttribute("aria-expanded", "true");
  }

  function closeBox() {
    box.style.display = "none";
    box.dataset.open = "false";
    btn.textContent = LABEL_OPEN;
    btn.setAttribute("aria-expanded", "false");
  }

  function setLoading() {
    box.innerHTML = `
      <div class="md-explain-loading">
        <span class="md-spinner" aria-hidden="true"></span>
        <span>${LABEL_LOADING}</span>
      </div>
    `;
    openBox();
  }

  btn.addEventListener("click", async () => {
    // 이미 열려 있으면 닫기
    if (box.dataset.open === "true") {
      closeBox();
      return;
    }

    // 이미 로드했으면 재사용해서 열기
    if (box.dataset.loaded === "true") {
      openBox();
      return;
    }

    // 최초 1회만 API 호출
    btn.disabled = true;
    setLoading();

    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movie_id: btn.dataset.movieId,
          title: btn.dataset.title,
          genres: btn.dataset.genres,
          year: btn.dataset.year,
        }),
      });

      if (!res.ok) throw new Error("API request failed");

      const data = await res.json();
      const text = data && data.explanation ? String(data.explanation).trim() : "";

      if (!text) throw new Error("Empty explanation");

      box.textContent = text;
      box.dataset.loaded = "true";
      openBox();
    } catch (err) {
      box.textContent = "We couldn’t load the recommendation details. Please try again later.";
      openBox();
    } finally {
      btn.disabled = false;
    }
  });
});
