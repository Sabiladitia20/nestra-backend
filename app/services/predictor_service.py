"""
PLTB Predictor Service
========================
Singleton wrapper around WindPredictor for wind speed forecasting.
Provides dependency injection and safe path resolution.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

# ── Resolve pltb_artifacts path and make it importable ──────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_ARTIFACTS_DIR: Optional[Path] = None


def _resolve_artifacts_dir() -> Path:
    """Resolve the pltb_artifacts directory, configurable via settings."""
    global _ARTIFACTS_DIR
    if _ARTIFACTS_DIR is not None:
        return _ARTIFACTS_DIR

    try:
        from app.core.config import get_settings
        settings = get_settings()
        configured = getattr(settings, "PLTB_ARTIFACTS_DIR", "./pltb_artifacts")
    except Exception:
        configured = "./pltb_artifacts"

    candidate = Path(configured)
    if not candidate.is_absolute():
        candidate = _BACKEND_DIR / candidate

    _ARTIFACTS_DIR = candidate.resolve()
    return _ARTIFACTS_DIR


class PredictorService:
    """
    Wraps WindPredictor from pltb_artifacts/predict_pltb.py.

    - Lazy-loads the predictor on first use
    - Reads ranking.json and final_metrics.csv
    - Thread-safe singleton via module-level factory
    """

    def __init__(self):
        self._predictor = None
        self._ranking_cache: Optional[List[Dict[str, Any]]] = None
        self._metrics_cache: Optional[List[Dict[str, Any]]] = None
        self._locations_cache: Optional[List[Dict[str, Any]]] = None
        self._artifacts_dir: Optional[Path] = None
        logger.info("PredictorService created (lazy-load mode)")

    # ── Internal helpers ────────────────────────────────────────────────────

    @property
    def artifacts_dir(self) -> Path:
        if self._artifacts_dir is None:
            self._artifacts_dir = _resolve_artifacts_dir()
        return self._artifacts_dir

    def _ensure_predictor(self):
        """Import and initialise WindPredictor on first call."""
        if self._predictor is not None:
            return

        artifacts = self.artifacts_dir
        if not artifacts.exists():
            raise FileNotFoundError(
                f"pltb_artifacts directory not found: {artifacts}"
            )

        # Add pltb_artifacts to sys.path so we can import predict_pltb
        artifacts_str = str(artifacts)
        if artifacts_str not in sys.path:
            sys.path.insert(0, artifacts_str)

        try:
            from predict_pltb import WindPredictor  # type: ignore
        except ImportError as exc:
            logger.error(f"Cannot import WindPredictor: {exc}")
            raise RuntimeError(
                f"Failed to import predict_pltb from {artifacts}: {exc}"
            ) from exc

        logger.info(f"Initialising WindPredictor from {artifacts} ...")
        self._predictor = WindPredictor(str(artifacts))
        logger.info(
            f"WindPredictor ready — "
            f"{len(self._predictor.locations)} locations loaded, "
            f"min_history={self._predictor.min_history}h"
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def predict(
        self,
        location: str,
        recent_ws10m: List[float],
        target_time: str,
    ) -> Dict[str, Any]:
        """
        Run wind speed prediction for a given location.

        Raises:
            KeyError  – unknown location
            ValueError – insufficient history, NaN values, etc.
        """
        self._ensure_predictor()
        result = self._predictor.predict(location, recent_ws10m, target_time)
        logger.info(
            f"Prediction OK — {location} → "
            f"{result['predicted_ws10m']} m/s @ {target_time}"
        )
        return result

    def get_ranking(self) -> List[Dict[str, Any]]:
        """Return site ranking from ranking.json (cached)."""
        if self._ranking_cache is None:
            ranking_path = self.artifacts_dir / "ranking.json"
            if not ranking_path.exists():
                raise FileNotFoundError(f"ranking.json not found: {ranking_path}")
            with open(ranking_path, encoding="utf-8") as f:
                self._ranking_cache = json.load(f)
            logger.info(f"Loaded ranking.json — {len(self._ranking_cache)} sites")
        return self._ranking_cache

    def get_locations(self) -> List[Dict[str, Any]]:
        """Return available locations from model_registry.json."""
        if self._locations_cache is None:
            self._ensure_predictor()
            locations = []
            for loc_id, meta in self._predictor.locations.items():
                locations.append({
                    "id": loc_id,
                    "name": meta.get("name", loc_id.title()),
                    "scenario": meta.get("scenario", ""),
                    "status": meta.get("status", ""),
                    "metrics": meta.get("metrics", {}),
                    "feature_count": len(meta.get("feature_order", [])),
                })
            self._locations_cache = locations
            logger.info(f"Locations list built — {len(locations)} entries")
        return self._locations_cache

    def get_metrics(self) -> List[Dict[str, Any]]:
        """Return final_metrics.csv as list of dicts."""
        if self._metrics_cache is None:
            metrics_path = self.artifacts_dir / "final_metrics.csv"
            if not metrics_path.exists():
                raise FileNotFoundError(
                    f"final_metrics.csv not found: {metrics_path}"
                )
            with open(metrics_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self._metrics_cache = list(reader)
            logger.info(
                f"Loaded final_metrics.csv — {len(self._metrics_cache)} rows"
            )
        return self._metrics_cache

    @property
    def min_history(self) -> int:
        """Minimum number of historical hours required for prediction."""
        self._ensure_predictor()
        return self._predictor.min_history


# ── Singleton ───────────────────────────────────────────────────────────────

_predictor_service: Optional[PredictorService] = None


def get_predictor_service() -> PredictorService:
    """Get or create the PredictorService singleton."""
    global _predictor_service
    if _predictor_service is None:
        _predictor_service = PredictorService()
    return _predictor_service
