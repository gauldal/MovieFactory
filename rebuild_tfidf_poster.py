import os
import pickle
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import save_npz

# 프로젝트 기준 경로
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_CSV = PROJECT_ROOT / "moviefactory" / "data" / "movie_clean_data_poster.csv"
OUT_DIR = PROJECT_ROOT / "moviefactory" / ".cache" / "full_working" / "tfidf"
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_CSV)
df.fillna({"title": "", "overview": ""}, inplace=True)

# 텍스트 구성(간단/안정)
texts = (df["title"].astype(str) + " " + df["overview"].astype(str)).tolist()

vectorizer = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2),
    stop_words="english",
)

matrix = vectorizer.fit_transform(texts)

# 저장(세트로!)
save_npz(OUT_DIR / "tfidf_matrix.npz", matrix)
with open(OUT_DIR / "tfidf_vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("OK")
print("rows:", matrix.shape[0], "cols:", matrix.shape[1])
print("saved:", OUT_DIR)
