# moviefactory/eval/find_movie_id.py

from __future__ import annotations
import sys
from moviefactory.engine.engine_provider import get_runtime_engine


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m moviefactory.eval.find_movie_id "<keyword>"')
        print('Example: python -m moviefactory.eval.find_movie_id "mars"')
        return

    keyword = " ".join(sys.argv[1:]).strip()
    if not keyword:
        print("Empty keyword.")
        return

    engine = get_runtime_engine()
    df = engine.df

    mask = df["title"].astype(str).str.lower().str.contains(keyword.lower(), regex=False)
    hits = df[mask][["movie_id", "title", "release_date"]].head(50)

    if hits.empty:
        print("(no matches)")
        return

    for _, r in hits.iterrows():
        try:
            mid = int(r["movie_id"])
        except Exception:
            mid = r["movie_id"]
        print(mid, "|", str(r["title"]), "|", str(r["release_date"]))


if __name__ == "__main__":
    main()
