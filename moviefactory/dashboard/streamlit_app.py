import streamlit as st
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import plotly.express as px
import requests

# ===============================
# PATH
# ===============================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / ".cache"

MOVIE_CSV = DATA_DIR / "movie_clean_data.csv"
SBERT_PKL = CACHE_DIR / "sbert_embeddings.pkl"
TFIDF_PKL = CACHE_DIR / "tfidf_matrix.pkl"
CF_PKL = CACHE_DIR / "cf_matrix.pkl"

DASHBOARD_API = "http://localhost:5000/api/dashboard/metrics"

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="MovieFactory Analytics Dashboard",
    layout="wide"
)

st.title("MovieFactory Analytics Dashboard")
st.caption(
    "Visualization-first analytics explaining how SBERT, CLIP, TF-IDF and "
    "Collaborative Filtering are combined in the hybrid engine."
)

# ===============================
# LOADERS
# ===============================
@st.cache_data
def load_movies():
    return pd.read_csv(MOVIE_CSV)

@st.cache_data
def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)

@st.cache_data
def load_metrics():
    resp = requests.get(DASHBOARD_API, timeout=3)
    resp.raise_for_status()
    return resp.json()

movies_df = load_movies()
metrics = load_metrics()

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("Controls")

heatmap_n = st.sidebar.slider(
    "Heatmap size (N x N)",
    min_value=10,
    max_value=40,
    value=20,
    step=5
)

# ===============================
# SECTION 1: SEARCH INPUT METRICS
# ===============================
st.subheader("1. Search Input Distribution")

search_input = metrics["search_input"]

df_input = pd.DataFrame([
    {"type": k, "ratio": v}
    for k, v in search_input["type_ratio"].items()
])

fig_input = px.bar(
    df_input,
    x="type",
    y="ratio",
    title="Search Type Ratio"
)
st.plotly_chart(fig_input, use_container_width=True)

st.markdown(
    """
**Explanation**  
This chart shows how users interact with the system:
text search, image search, and hybrid queries.
"""
)

# ===============================
# SECTION 2: ENGINE SCORE CONTRIBUTION
# ===============================
st.subheader("2. Engine Score Contribution")

engine_scores = metrics["engine_scores"]

df_engine = pd.DataFrame([
    {"engine": k, "score": v}
    for k, v in engine_scores.items()
])

fig_engine = px.bar(
    df_engine,
    x="engine",
    y="score",
    title="Average Engine Contribution"
)
st.plotly_chart(fig_engine, use_container_width=True)

st.markdown(
    """
**Explanation**  
Each bar represents the average contribution of an individual engine
(SBERT, CLIP, TF-IDF, CF) before hybrid aggregation.
"""
)

# ===============================
# SECTION 3: HYBRID WEIGHT VISUALIZATION
# ===============================
st.subheader("3. Hybrid Weight Configuration")

hybrid = metrics["hybrid"]

df_hybrid = pd.DataFrame([
    {"signal": k, "weight": v}
    for k, v in hybrid["weights"].items()
])

fig_hybrid = px.pie(
    df_hybrid,
    names="signal",
    values="weight",
    title="Hybrid Weight Distribution"
)
st.plotly_chart(fig_hybrid, use_container_width=True)

st.markdown(
    """
**Explanation**  
This pie chart visualizes how different signals are weighted
inside the hybrid recommendation engine.
"""
)

# ===============================
# SECTION 4: SBERT SIMILARITY HEATMAP
# ===============================
st.subheader("4. SBERT Semantic Similarity Heatmap (Primary)")

sbert_embeddings = load_pickle(SBERT_PKL)
idx = np.random.choice(len(sbert_embeddings), heatmap_n, replace=False)
emb = sbert_embeddings[idx]
titles = movies_df.iloc[idx]["title"].values

sim = cosine_similarity(emb)
df_sim = pd.DataFrame(sim, index=titles, columns=titles)

fig_sbert = px.imshow(
    df_sim,
    color_continuous_scale="RdBu",
    zmin=-1,
    zmax=1,
    title="SBERT Cosine Similarity"
)
fig_sbert.update_layout(height=600)
st.plotly_chart(fig_sbert, use_container_width=True)

# ===============================
# SECTION 5: CF SIMILARITY HEATMAP
# ===============================
st.subheader("5. Collaborative Filtering Similarity Heatmap")

cf_matrix = load_pickle(CF_PKL)
cf_n = min(heatmap_n, cf_matrix.shape[0])
cf_sample = cf_matrix[:cf_n, :cf_n]
cf_titles = movies_df.iloc[:cf_n]["title"].values

df_cf = pd.DataFrame(cf_sample, index=cf_titles, columns=cf_titles)

fig_cf = px.imshow(
    df_cf,
    color_continuous_scale="Viridis",
    title="CF Similarity Matrix"
)
fig_cf.update_layout(height=450)
st.plotly_chart(fig_cf, use_container_width=True)

# ===============================
# SECTION 6: CACHE STATUS
# ===============================
st.subheader("6. Engine Cache Status")

status_data = {
    "SBERT Cache": SBERT_PKL.exists(),
    "TF-IDF Cache": TFIDF_PKL.exists(),
    "CF Cache": CF_PKL.exists(),
    "Total Movies": len(movies_df),
}

st.table(
    pd.DataFrame.from_dict(
        status_data,
        orient="index",
        columns=["Status"]
    )
)
