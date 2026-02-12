document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-explain");
  const box = document.getElementById("explanation-result");

  if (!btn || !box) return;

  // 초기 상태
  box.style.display = "none";
  box.dataset.loaded = "false";
  box.dataset.open = "false";

  btn.addEventListener("click", async () => {

    /* ===============================
       1. 이미 열려 있으면 → 닫기
    =============================== */
    if (box.dataset.open === "true") {
      box.style.display = "none";
      box.dataset.open = "false";
      return;
    }

    /* ===============================
       2. 이미 불러온 설명이면 → 재사용
    =============================== */
    if (box.dataset.loaded === "true") {
      box.style.display = "block";
      box.dataset.open = "true";
      return;
    }

    /* ===============================
       3. 최초 1회만 API 호출
    =============================== */
    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          movie_id: btn.dataset.movieId,
          title: btn.dataset.title,
          genres: btn.dataset.genres,
          year: btn.dataset.year,
        }),
      });

      if (!res.ok) {
        throw new Error("API request failed");
      }

      const data = await res.json();

      if (!data || !data.explanation) {
        throw new Error("Invalid response");
      }

      // 결과 표시
      box.innerText = data.explanation;
      box.style.display = "block";

      // 상태 고정 (재호출 방지)
      box.dataset.loaded = "true";
      box.dataset.open = "true";

    } catch (err) {
      box.innerText = "설명을 불러오지 못했습니다.";
      box.style.display = "block";
      box.dataset.open = "true";
    }
  });
});
