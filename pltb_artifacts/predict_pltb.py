"""Inference module PLTB wind-speed forecasting (Random Forest). Backend-ready (FastAPI)."""
from __future__ import annotations
import json, os, warnings
from datetime import datetime
import numpy as np, pandas as pd, joblib, sklearn


HF_REPO_ID = "sabilditia/nestra-models"  # ← sesuaikan username HuggingFace kamu


def _download_model_if_missing(model_filename: str, dest_dir: str) -> str:
    """Download model dari HuggingFace kalau belum ada lokal."""
    dest_path = os.path.join(dest_dir, model_filename)
    if not os.path.exists(dest_path):
        from huggingface_hub import hf_hub_download
        print(f"[HF] Downloading {model_filename} ...")
        hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=model_filename,
            repo_type="model",
            local_dir=dest_dir,
        )
        print(f"[HF] ✅ {model_filename} selesai")
    return dest_path


class WindPredictor:
    """Registry 5 model RF per lokasi. Lazy-load + cache. Satu interface predict()."""

    def __init__(self, artifact_dir: str):
        self.dir = artifact_dir
        with open(os.path.join(artifact_dir, "model_registry.json")) as f:
            reg = json.load(f)
        with open(os.path.join(artifact_dir, "preprocessing_recipe.json")) as f:
            self.recipe = json.load(f)
        self.locations = reg["locations"]
        self.horizon = reg.get("horizon_hours", 1)
        self._check_versions(reg.get("library_versions", {}))
        self._cache = {}
        r = self.recipe
        self.min_history = max(r["lags"] + r["rolling_mean_windows"] + r["rolling_std_windows"])

    def _check_versions(self, saved):
        cur = sklearn.__version__
        if saved.get("scikit_learn") and saved["scikit_learn"] != cur:
            warnings.warn(f"sklearn mismatch: model dilatih {saved['scikit_learn']}, "
                          f"backend {cur}. Samakan versi agar aman.")

    # ↓↓↓ METHOD YANG DIGANTI — download dari HuggingFace kalau tidak ada lokal ↓↓↓
    def _model(self, loc_id):
        if loc_id not in self._cache:
            model_filename = os.path.basename(self.locations[loc_id]["model_file"])
            models_dir = os.path.join(self.dir, "models")
            os.makedirs(models_dir, exist_ok=True)
            local_path = os.path.join(models_dir, model_filename)
            _download_model_if_missing(model_filename, models_dir)
            self._cache[loc_id] = joblib.load(local_path)
        return self._cache[loc_id]
    # ↑↑↑ SAMPAI SINI ↑↑↑

    def _build_row(self, ws_hist, target_dt, feature_order):
        ws = np.asarray(ws_hist, dtype=float)
        if np.isnan(ws).any():
            raise ValueError("recent_ws10m mengandung NaN.")
        if len(ws) < self.min_history:
            raise ValueError(f"Riwayat kurang: butuh >= {self.min_history} jam, ada {len(ws)}.")
        r = self.recipe
        if feature_order == [r["s0_dummy_col"]]:
            return pd.DataFrame([[1.0]], columns=feature_order)
        feat = {}
        for k in r["lags"]:
            feat[f"WS10M_lag{k}"] = ws[-k]
        for w in r["rolling_mean_windows"]:
            feat[f"WS10M_roll{w}"] = ws[-w:].mean()
        for w in r["rolling_std_windows"]:
            feat[f"WS10M_std{w}"] = ws[-w:].std(ddof=1)
        ch = r["cyclical"]["hour"]
        feat["target_hour_sin"] = np.sin(2*np.pi*target_dt.hour/ch["period"])
        feat["target_hour_cos"] = np.cos(2*np.pi*target_dt.hour/ch["period"])
        if r.get("use_month_cyclical"):
            cm = r["cyclical"]["month"]; sub = 1 if cm["subtract_one"] else 0
            feat["target_month_sin"] = np.sin(2*np.pi*(target_dt.month-sub)/cm["period"])
            feat["target_month_cos"] = np.cos(2*np.pi*(target_dt.month-sub)/cm["period"])
        missing = [c for c in feature_order if c not in feat]
        if missing:
            raise ValueError(f"Fitur tak terbentuk: {missing}")
        return pd.DataFrame([[feat[c] for c in feature_order]], columns=feature_order)

    def predict(self, location: str, recent_ws10m, target_time: str) -> dict:
        if location not in self.locations:
            raise KeyError(f"Lokasi '{location}' tidak ada. Pilihan: {list(self.locations)}")
        meta = self.locations[location]
        target_dt = datetime.fromisoformat(target_time)
        X = self._build_row(recent_ws10m, target_dt, meta["feature_order"])
        pred = float(self._model(location).predict(X)[0])
        return {
            "location": location,
            "target_time": target_time,
            "predicted_ws10m": round(max(pred, 0.0), 4),
            "unit": "m/s",
            "scenario": meta["scenario"],
            "model_confidence_r2": meta["metrics"]["r2"],
            "model_test_mae": meta["metrics"]["mae"],
        }