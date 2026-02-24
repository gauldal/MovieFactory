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

// ChartDataLabels plugin 등록 (CDN 로드되어 있으면 전역에 존재)
function registerChartPlugins() {
  try {
    if (window.Chart && window.ChartDataLabels) {
      Chart.register(ChartDataLabels);
    }
  } catch (e) {
    // plugin 없으면 조용히 무시
  }
}

document.addEventListener("DOMContentLoaded", () => {
  registerChartPlugins();
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
      maintainAspectRatio: false,
      plugins: {
        datalabels: { display: false }   // ✅ 여기!
      }
    }
  });
}

/* =========================================================
   Recommendation Analysis (v1.6)
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

  // ✅ ab_meta 표시 (스샷/재현성)
  const metaEl = document.getElementById("abMeta");
  if (metaEl) {
    if (data.ab_meta) {
      const m = data.ab_meta;
      metaEl.textContent =
        `sessions=${m.n_sessions} | top_k=${m.top_k} | sort=${m.sort} | candidate_k=${m.candidate_k}`;
    } else {
      metaEl.textContent = "";
    }
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

  const labels = Object.keys(rankerData);
  const offVals = labels.map(e => Number(rankerData[e]?.off ?? 0));
  const onVals = labels.map(e => Number(rankerData[e]?.on ?? 0));

  if (rankerComparisonChart) rankerComparisonChart.destroy();

  // ✅ Tooltip에 Δ(ON - OFF) 표시
  const tooltipCallbacks = {
    callbacks: {
      afterBody: (tooltipItems) => {
        const item = tooltipItems?.[0];
        if (!item) return "";

        const idx = item.dataIndex;
        const chart = item.chart;

        const dsOff = chart.data.datasets.find(d => d.label === "Ranker OFF");
        const dsOn = chart.data.datasets.find(d => d.label === "Ranker ON");

        const off = Number(dsOff?.data?.[idx] ?? 0);
        const on = Number(dsOn?.data?.[idx] ?? 0);

        const delta = on - off;
        const sign = delta >= 0 ? "+" : "";
        return `Δ (ON - OFF): ${sign}${delta.toFixed(3)}`;
      }
    }
  };

  const hasDatalabels = !!(window.ChartDataLabels);

  rankerComparisonChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Ranker OFF", data: offVals },
        { label: "Ranker ON", data: onVals }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: tooltipCallbacks,
        // ✅ 막대 위에 값 표시(스샷용). plugin이 있을 때만 동작
        datalabels: hasDatalabels ? {
          anchor: "end",
          align: "end",
          formatter: (value) => Number(value).toFixed(2)
        } : undefined
      }
    }
  });

  // ✅ 항상 보이는 Δ 요약(스샷용) — 반드시 함수 내부에 있어야 engines/offVals/onVals 사용 가능
  const deltaEl = document.getElementById("abDeltaSummary");
  if (deltaEl) {
    const deltas = labels.map((_, i) => onVals[i] - offVals[i]);
    const pos = deltas.filter(d => d > 0).length;
    const neg = deltas.filter(d => d < 0).length;
    const avgDelta = deltas.length ? (deltas.reduce((a,b)=>a+b,0) / deltas.length) : 0;
    const sign = avgDelta >= 0 ? "+" : "";


  }
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
  const query = document.getElementById("text-query-input")?.value?.trim();
  if (!query) return;

  setEngineStatus("panel-tfidf", "Searching...");
  setEngineStatus("panel-sbert", "Searching...");
  // CLIP은 텍스트 검색과 무관하므로 그대로 둠

  const res = await fetch("/api/dashboard/engine_comparison/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });

  const data = await res.json();

  const tfidf = data.results?.["TF-IDF"] || [];
  const sbert = data.results?.["SBERT"] || [];

  // ✅ Overlap(교집합) 하이라이트
  const tfidfIds = toIdSet(tfidf);
  const sbertIds = toIdSet(sbert);
  const overlapIds = intersection(tfidfIds, sbertIds);

  // ✅ 점수 bar 렌더링(패널 내부 max 기준)
  renderEngineResults("panel-tfidf", tfidf, { highlightIds: overlapIds });
  renderEngineResults("panel-sbert", sbert, { highlightIds: overlapIds });
}

/* =========================================================
   Engine Comparison — Image (CLIP)
========================================================= */

async function onImageSearch() {
  const input = document.getElementById("image-query-input");
  if (!input?.files?.length) return;

  setEngineStatus("panel-clip", "Searching...");

  const fd = new FormData();
  fd.append("image", input.files[0]);

  const res = await fetch("/api/dashboard/search/image", {
    method: "POST",
    body: fd
  });

  const data = await res.json();

  // 이미지 검색은 현재 CLIP 단독이므로 overlap 하이라이트는 적용하지 않음
  renderEngineResults("panel-clip", data.results || [], { highlightIds: new Set() });
}

/* =========================================================
   🔑 Engine Result Rendering (4개 구조 시절 UI 복원 + Bar + Overlap)
========================================================= */

function renderEngineResults(panelId, results, { highlightIds = new Set() } = {}) {
  const panel = document.getElementById(panelId);
  if (!panel) return;

  const resultsBox = panel.querySelector(".mf-engine-results");
  const statusBox = panel.querySelector(".mf-engine-status");

  if (statusBox) statusBox.textContent = "";
  if (resultsBox) resultsBox.innerHTML = "";

  if (!results || results.length === 0) {
    if (statusBox) statusBox.textContent = "No results";
    return;
  }

  const items = results.slice(0, 5);

  if (statusBox) statusBox.textContent = `Top ${items.length}`;

  // 패널 내부 상대 스케일: maxScore 기준으로 bar 비율 계산
  const maxScore = Math.max(...items.map(x => Number(x?.score) || 0), 0) || 1;

  items.forEach((item, idx) => {
    const title = item?.title ?? "Unknown";
    const score = Number(item?.score) || 0;
    const movieId = item?.movie_id != null ? String(item.movie_id) : "";

    const pct = Math.max(0, Math.min(100, (score / maxScore) * 100));

    const ratio = score / maxScore;
    let scoreClass = "score-low";
    if (ratio >= 0.66) scoreClass = "score-high";
    else if (ratio >= 0.33) scoreClass = "score-mid";

    const row = document.createElement("div");
    row.className = "mf-engine-item";

    // ✅ overlap 강조
    if (movieId && highlightIds.has(movieId)) {
      row.classList.add("is-overlap");
    }

    row.innerHTML = `
      <div class="mf-engine-item-top">
        <div class="mf-engine-item-title">${idx + 1}. ${escapeHtml(title)}</div>
        <div class="mf-engine-item-score">${score.toFixed(3)}</div>
      </div>
      <div class="mf-engine-bar">
        <div class="mf-engine-bar-fill ${scoreClass}" style="width:${pct}%"></div>
      </div>
    `;

    resultsBox?.appendChild(row);
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

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function toIdSet(items) {
  return new Set((items || []).map(x => String(x?.movie_id ?? "")).filter(Boolean));
}

function intersection(a, b) {
  const out = new Set();
  for (const v of a) if (b.has(v)) out.add(v);
  return out;
}