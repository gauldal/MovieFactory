"""
Engine Provider
---------------

RuntimeEngine 싱글톤 접근용 Provider

- Web(App)
- Dashboard
- Metrics
- 기타 서비스 레이어

공통으로 동일한 RuntimeEngine 인스턴스를 사용하도록 보장한다.

✅ 정책(최종 고정)
- 캐시 루트는 기본적으로 .cache/full_working 을 사용한다.
- canonical CSV는 기본적으로 movie_clean_data_poster.csv 를 사용한다.
- 단, 사용자가 환경변수로 명시하면 그 값을 우선한다.
"""

from __future__ import annotations

import os
from typing import Optional

# ==================================================
# 🔑 환경 고정(엔진 import 전에!)
# ==================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # moviefactory/
DEFAULT_CACHE_ROOT = os.path.join(BASE_DIR, ".cache", "full_working")

if not os.environ.get("MOVIEFACTORY_CACHE_ROOT"):
    os.environ["MOVIEFACTORY_CACHE_ROOT"] = DEFAULT_CACHE_ROOT

if not os.environ.get("MOVIEFACTORY_CACHE_MODE"):
    os.environ["MOVIEFACTORY_CACHE_MODE"] = "FULL_WORKING"

if not os.environ.get("MOVIEFACTORY_CANONICAL_CSV"):
    os.environ["MOVIEFACTORY_CANONICAL_CSV"] = "movie_clean_data_poster.csv"

_printed = False


def _print_boot_config_once():
    global _printed
    if _printed:
        return
    _printed = True
    try:
        print(
            "[EngineProvider] "
            f"CACHE_ROOT={os.environ.get('MOVIEFACTORY_CACHE_ROOT')} | "
            f"CACHE_MODE={os.environ.get('MOVIEFACTORY_CACHE_MODE')} | "
            f"CANONICAL_CSV={os.environ.get('MOVIEFACTORY_CANONICAL_CSV')}"
        )
    except Exception:
        pass


from moviefactory.engine.runtime_engine import RuntimeEngine  # noqa: E402

_runtime_engine: Optional[RuntimeEngine] = None


def get_runtime_engine() -> RuntimeEngine:
    """
    RuntimeEngine 싱글톤을 반환한다.
    - 최초 호출 시 1회 생성
    - 이후 동일 인스턴스 재사용
    """
    global _runtime_engine
    if _runtime_engine is None:
        _print_boot_config_once()
        _runtime_engine = RuntimeEngine()
    return _runtime_engine
