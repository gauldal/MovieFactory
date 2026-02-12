# moviefactory/eval/find_by_overview.py

from __future__ import annotations
import sys
from moviefactory.engine.engine_provider import get_runtime_engine

def main():
    if len(sys.argv) < 2:
        print('Usage: python -m moviefactory.eval.find_by_overview "<keyword>"')
        print('Example: python -m moviefactory.eval.find_by_overview "vigilante"')
        return

    keyword = " ".join(sys.argv[1:]).strip().lower()
    engine = get_runtime_engine()
    df = engine.df

    title = df["title"].astype(str).str.lower()
    overview = df["overview"].astype(str).str.lower()
    tagline = df["tagline"].astype(str).str.lower()

    mask = title.str.contains(keyword, regex=False) | overview.str.contains(keyword, regex=False) | tagline.str.contains(keyword, regex=False)

    hits = df[mask][["movie_id", "title", "release_date"]].head(50)

    if hits.empty:
        print("(no matches)")
        return

    for _, r in hits.iterrows():
        print(int(r["movie_id"]), "|", str(r["title"]), "|", str(r["release_date"]))

if __name__ == "__main__":
    main()
