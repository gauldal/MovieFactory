import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(r"C:\IT\moviefactory\movie_factory_project")

POSTER_CSV = PROJECT_ROOT / "moviefactory" / "data" / "movie_clean_data_poster.csv"
FULL_CSV   = PROJECT_ROOT / "moviefactory" / "data" / "movie_clean_data.csv"

CACHE_ROOT = PROJECT_ROOT / "moviefactory" / ".cache" / "full_working"
SBERT_DIR  = CACHE_ROOT / "sbert"
SBERT_DIR.mkdir(parents=True, exist_ok=True)

FULL_EMB = SBERT_DIR / "sbert_embeddings.npy"  # 기존 전체 임베딩(18901) 파일
OUT_EMB  = SBERT_DIR / "sbert_embeddings.npy"  # 같은 이름으로 덮어쓰기(=poster 기준으로 통일)

# 1) poster movie_ids
poster_df = pd.read_csv(POSTER_CSV)
poster_ids = [int(x) for x in poster_df["movie_id"].tolist()]

# 2) full movie_ids (임베딩의 행 순서를 알려주는 기준)
full_df = pd.read_csv(FULL_CSV)
full_ids = [int(x) for x in full_df["movie_id"].tolist()]
id_to_idx = {mid: i for i, mid in enumerate(full_ids)}

# 3) full embeddings
emb = np.load(FULL_EMB)
if emb.shape[0] != len(full_ids):
    raise RuntimeError(f"Row mismatch: embeddings rows={emb.shape[0]} vs full_csv rows={len(full_ids)}")

# 4) subset in poster order
idx = []
missing = []
for mid in poster_ids:
    i = id_to_idx.get(mid)
    if i is None:
        missing.append(mid)
    else:
        idx.append(i)

subset = emb[np.array(idx)]

# 5) save (overwrite)
np.save(OUT_EMB, subset)

print("OK")
print("poster_ids:", len(poster_ids))
print("subset_rows:", subset.shape[0], "dim:", subset.shape[1])
print("missing_ids:", len(missing))
if missing[:10]:
    print("missing_sample:", missing[:10])
print("saved:", OUT_EMB)
