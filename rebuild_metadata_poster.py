import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(r"C:\IT\moviefactory\movie_factory_project")
CSV = PROJECT_ROOT / "moviefactory" / "data" / "movie_clean_data_poster.csv"
CACHE_ROOT = PROJECT_ROOT / "moviefactory" / ".cache" / "full_working"
OUT = CACHE_ROOT / "metadata.json"

df = pd.read_csv(CSV)
movie_ids = [int(x) for x in df["movie_id"].tolist()]

CACHE_ROOT.mkdir(parents=True, exist_ok=True)

payload = {
    "dataset": "poster",
    "movie_ids": movie_ids,
    "count": len(movie_ids),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("OK:", OUT, "count=", len(movie_ids))
