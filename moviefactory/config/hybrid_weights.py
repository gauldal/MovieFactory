# moviefactory/config/hybrid_weights.py
# MovieFactory v1.x — Hybrid weight configuration

# 검색 타입별 preset
HYBRID_WEIGHTS = {
    "text": {
        "tfidf": 0.4,
        "sbert": 0.6,
        "clip": 0.0,
        "cf": 0.0,
    },
    "image": {
        "tfidf": 0.0,
        "sbert": 0.0,
        "clip": 1.0,
        "cf": 0.0,
    },
    "reco": {
        "tfidf": 0.0,
        "sbert": 0.0,
        "clip": 0.0,
        "cf": 1.0,
    },
}
