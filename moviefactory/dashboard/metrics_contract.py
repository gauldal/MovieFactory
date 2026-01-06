"""
Dashboard Metrics Contract (v1)

Purpose:
- Define the shape and meaning of dashboard metrics
- NOT a live service
- NOT a production analytics pipeline
- Used for explanation, evaluation, and presentation only
"""

from typing import Dict, Any, List


def get_search_input_metrics() -> Dict[str, Any]:
    """
    Search input distribution (illustrative)
    """
    return {
        "search_type_ratio": {
            "text": 70,
            "image": 30,
        },
        "keyword_length_distribution": [1, 2, 3, 4, 5],
    }


def get_engine_score_metrics() -> Dict[str, Any]:
    """
    Individual engine score distributions (illustrative)
    """
    return {
        "sbert_scores": [0.12, 0.45, 0.67, 0.82],
        "clip_scores": [0.10, 0.33, 0.58, 0.74],
        "cf_scores": [0.05, 0.20, 0.41, 0.60],
    }


def get_hybrid_metrics() -> Dict[str, Any]:
    """
    Hybrid score composition (illustrative)
    """
    return {
        "weights": {
            "sbert": 0.4,
            "clip": 0.3,
            "cf": 0.3,
        },
        "hybrid_scores": [0.25, 0.48, 0.66, 0.81],
    }


def get_ranking_metrics() -> Dict[str, Any]:
    """
    Ranking comparison and shift (illustrative)
    """
    return {
        "rank_comparison": [
            {"engine_rank": 5, "hybrid_rank": 2},
            {"engine_rank": 10, "hybrid_rank": 6},
        ],
        "rank_shift_distribution": [-3, -2, 0, 1, 3],
    }


def get_all_dashboard_metrics() -> Dict[str, Any]:
    """
    Aggregated metrics contract (single entry point)
    """
    return {
        "search_input": get_search_input_metrics(),
        "engine_scores": get_engine_score_metrics(),
        "hybrid": get_hybrid_metrics(),
        "ranking": get_ranking_metrics(),
    }
