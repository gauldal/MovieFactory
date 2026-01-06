"""
Dashboard API
=============
- 책임: 대시보드용 메트릭 JSON 제공
- 데이터 출처: metrics_contract.py
- 실시간 계산 없음 (설명/시각화용)
"""

from flask import Blueprint, jsonify
from moviefactory.contracts.metrics_contract import METRICS_CONTRACT

dashboard_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Return dashboard metrics contract as JSON.
    Used by Streamlit analytics dashboard.
    """
    return jsonify(METRICS_CONTRACT)
