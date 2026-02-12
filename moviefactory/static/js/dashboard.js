/* =========================================================
   MovieFactory Dashboard JS
   CONTRACT:
   - dashboard.html 구조 절대 변경 ❌
   - DOM 생성은 mf-engine-results 내부 item만 허용
   - 4개 구조 시절 회색 박스 UI 복원
========================================================= */

let yearChart = null;
let engineContributionChart = null;
let rankerComparisonChart = null;

document.addEventListener("DOMContentLoaded", () => {
  loadOverview();
  loadRecommendationAnalysis();
  bindSearchControls();
});

/* =========================================================
   Dataset Overview + Release Year Distribution
========================================================= */

async function loadOverview() {
  const res = await fetch("/api/dashboard/overview");
  const data = await res.json();

  setText("total-movies", data.total_movies, v => v.toLocaleString());
  setText("avg-rating", data.avg_rating, v => v.toFixed(2));
  setText("avg-popularity", data.avg_popularity, v => v.toFixed(2));
  setText("top20-rating", data.top20_avg_rating, v => v.toFixed(2));
  setText("recent-ratio", data.recent_10y_ratio, v => (v * 100).toFixed(1) + "%");

  if (data.year_distribution) {
    renderYearChart(data.year_distribution);
  }
}

function renderYearChart(years) {
  const ctx = document.getElementById("yearChart");
  if (!ctx) return;

  const labels = Object.keys(years).sort();
  const values = labels.map(y => years[y]);

  if (yearChart) yearChart.destroy();

  yearChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Movies", data: values }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
}

/* =========================================================
   Recommendation Analysis (v1.5)
========================================================= */

async function loadRecommendationAnalysis() {
  const res = await fetch("/api/dashboard/recommendation_analysis");
  const data = await res.json();

  if (data.engine_contribution) {
    renderEngineContribution(data.engine_contribution);
  }

  if (data.ranker_comparison) {
    renderRankerComparison(data.ranker_comparison);
  }
}

function renderEngineContribution(contrib) {
  const ctx = document.getElementById("engineContributionChart");
  if (!ctx) return;

  if (engineContributionChart) engineContributionChart.destroy();

  engineContributionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: Object.keys(contrib),
      datasets: [{ data: Object.values(contrib) }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
}

function renderRankerComparison(rankerData) {
  const ctx = document.getElementById("rankerComparisonChart");
  if (!ctx) return;

  const engines = Object.keys(rankerData);
  const offVals = engines.map(e => rankerData[e].off);
  const onVals = engines.map(e => rankerData[e].on);

  if (rankerComparisonChart) rankerComparisonChart.destroy();

  rankerComparisonChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: engines,
      datasets: [
        { label: "Ranker OFF", data: offVals },
        { label: "Ranker ON", data: onVals }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
}

/* =========================================================
   Search Controls
========================================================= */

function bindSearchControls() {
  document.getElementById("text-search-btn")
    ?.addEventListener("click", onTextSearch);

  document.getElementById("image-search-btn")
    ?.addEventListener("click", onImageSearch);
}

/* =========================================================
   Engine Comparison — Text (TF-IDF / SBERT)
========================================================= */

async function onTextSearch() {
  const query = document.getElementById("text-query-input").value.trim();
  if (!query) return;

  setEngineStatus("panel-tfidf", "Searching...");
  setEngineStatus("panel-sbert", "Searching...");

  const res = await fetch("/api/dashboard/engine_comparison/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });

  const data = await res.json();

  renderEngineResults("panel-tfidf", data.results?.["TF-IDF"]);
  renderEngineResults("panel-sbert", data.results?.["SBERT"]);
}

/* =========================================================
   Engine Comparison — Image (CLIP)
========================================================= */

async function onImageSearch() {
  const input = document.getElementById("image-query-input");
  if (!input.files.length) return;

  setEngineStatus("panel-clip", "Searching...");

  const fd = new FormData();
  fd.append("image", input.files[0]);

  const res = await fetch("/api/dashboard/search/image", {
    method: "POST",
    body: fd
  });

  const data = await res.json();
  renderEngineResults("panel-clip", data.results);
}

/* =========================================================
   🔑 Engine Result Rendering (4개 구조 시절 UI 복원)
========================================================= */

function renderEngineResults(panelId, results) {
  const panel = document.getElementById(panelId);
  if (!panel) return;

  const resultsBox = panel.querySelector(".mf-engine-results");
  const statusBox = panel.querySelector(".mf-engine-status");

  if (statusBox) statusBox.textContent = "";
  resultsBox.innerHTML = "";

  if (!results || results.length === 0) {
    statusBox.textContent = "No results";
    return;
  }

  results.slice(0, 5).forEach((item, idx) => {
    const row = document.createElement("div");

    /* 🔴 중요:
       이 클래스가 기존 CSS의
       회색 박스 / padding / 폰트 규칙을 담당 */
    row.className = "mf-engine-item";

    row.textContent =
      `${idx + 1}. ${item.title} (${item.score.toFixed(3)})`;

    resultsBox.appendChild(row);
  });
}

function setEngineStatus(panelId, text) {
  const panel = document.getElementById(panelId);
  if (!panel) return;

  const statusBox = panel.querySelector(".mf-engine-status");
  const resultsBox = panel.querySelector(".mf-engine-results");

  if (statusBox) statusBox.textContent = text;
  if (resultsBox) resultsBox.innerHTML = "";
}

/* =========================================================
   Helpers
========================================================= */

function setText(id, val, fmt) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = val != null ? fmt(val) : "–";
}
