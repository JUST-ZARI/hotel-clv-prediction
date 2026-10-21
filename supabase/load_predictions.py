"""
Load the model output (notebook 08) into Supabase for the dashboard.

    frontend/.venv/Scripts/python.exe supabase/load_predictions.py              (from the repo root)
    frontend/.venv/Scripts/python.exe supabase/load_predictions.py --no-models  (skip the model upload)

Run 004_predictions_dashboard.sql first. Uses the server (secret) key from
.streamlit/secrets.toml, so it bypasses RLS — run it only on your own machine.

What it writes
    guests           one row per guest (upsert by guest_id)
    model_runs       one row for this prediction run
    clv_predictions  one row per guest for this run (re-running replaces the run)
    ml-models bucket xgboost.json, random_forest.pkl, the metadata files and
                     snapshots/<run>.parquet — the guest list the dashboard downloads in one go

Only the newest KEEP_RUNS runs are kept so the free-tier database stays small.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import pandas as pd
from postgrest.types import CountMethod

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import auth  # noqa: E402  (reads .streamlit/secrets.toml through st.secrets)
from data import repository as repo  # noqa: E402  (snapshot name + columns the dashboard expects)

PREDICTIONS = ROOT / "data/processed/guest_predictions.csv.gz"
CLEANED = ROOT / "data/processed/cleaned_dataset.csv"
SUMMARY = ROOT / "results/evaluation_summary.json"
MODEL_FILES = ["models/xgboost.json", "models/random_forest.pkl", "models/training_metadata.json",
               "results/evaluation_summary.json"]
BUCKET = "ml-models"
BATCH = 1000
KEEP_RUNS = 2

GUEST_COLS = ["guest_id", "guest_email", "avg_daily_rate", "total_previous_stays", "cancellation_rate",
              "booking_channel", "last_stay_date", "avg_length_of_stay", "booking_lead_time", "is_repeat_guest",
              "guest_type", "first_stay_date", "market_segment", "hotel_type", "room_type", "meal_plan",
              "booking_canceled", "first_booking_year"]
PREDICTION_COLS = ["guest_id", "predicted_clv", "clv_tier", "tier_badge", "clv_percentile", "recommended_action",
                   "recommended_action_reason", "in_action_queue", "model_used", "predicted_at", "top_drivers"]


def records(df: pd.DataFrame) -> list[dict]:
    """JSON-ready rows: NaN → None, numpy types → Python types."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


def send(label: str, rows: list[dict], write) -> None:
    start = time.time()
    for i in range(0, len(rows), BATCH):
        write(rows[i:i + BATCH])
        done = min(i + BATCH, len(rows))
        print(f"\r  {label}: {done:,}/{len(rows):,}", end="", flush=True)
    print(f"  ({time.time() - start:.0f}s)")


def upload_snapshot(admin, df: pd.DataFrame, run_at: str) -> None:
    """The guest-list columns of this run as one compressed Parquet file (~2 MB)."""
    snap = df[list(repo.SNAPSHOT_COLUMNS)].copy()
    for col in repo.SNAPSHOT_CATEGORIES:
        snap[col] = snap[col].astype("category")
    data = snap.to_parquet(index=False, compression="zstd")
    admin.storage.from_(BUCKET).upload(repo.snapshot_path(run_at), data,
                                        {"content-type": "application/octet-stream", "upsert": "true"})
    print(f"  uploaded dashboard snapshot ({len(data) / 1e6:.1f} MB) to {BUCKET}/{repo.snapshot_path(run_at)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-models", action="store_true", help="skip uploading model files to Storage")
    parser.add_argument("--snapshot-only", action="store_true",
                        help="only (re)upload the dashboard snapshot for the run in guest_predictions.csv.gz")
    args = parser.parse_args()

    problem = auth.config_error()
    if problem:
        print("Supabase is not configured:", problem)
        return 1
    admin = auth._service_client()

    df = pd.read_csv(PREDICTIONS)
    extra = pd.read_csv(CLEANED, usecols=["guest_id", "room_type_reserved", "meal_plan", "is_canceled"])
    df = df.merge(extra.rename(columns={"room_type_reserved": "room_type"}).drop(columns="is_canceled"),
                  on="guest_id", how="left", validate="one_to_one")
    df["booking_canceled"] = df["is_canceled"].astype(bool)
    df["top_drivers"] = df["top_drivers"].map(json.loads)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    run_at = df["predicted_at"].iloc[0]
    if df["predicted_at"].nunique() != 1:
        print("guest_predictions.csv.gz holds more than one run; re-run notebook 08.")
        return 1
    print(f"Run {run_at}: {len(df):,} guests, model {summary['winner']}")
    if args.snapshot_only:
        upload_snapshot(admin, df, run_at)
        return 0

    # 1. guests (upsert keeps action logs that point at them)
    send("guests", records(df[GUEST_COLS]),
         lambda rows: admin.table("guests").upsert(rows, on_conflict="guest_id").execute())

    # 2. model run (replace this run's predictions if it was loaded before)
    t = summary["predicted_tier_thresholds_ksh"]
    m = summary["test_metrics"][summary["winner"]]
    admin.table("clv_predictions").delete().eq("predicted_at", run_at).execute()
    admin.table("model_runs").upsert({
        "predicted_at": run_at, "model_used": summary["winner"], "as_of_date": summary["as_of_date"],
        "high_min_clv": round(t["high_min"], 2), "low_max_clv": round(t["low_max"], 2),
        "platinum_min_clv": round(t["platinum_min"], 2),
        "test_mae": m["MAE"], "test_rmse": m["RMSE"], "test_r2": m["R2"], "guests_predicted": len(df),
    }, on_conflict="predicted_at").execute()

    # 3. predictions for this run
    send("clv_predictions", records(df[PREDICTION_COLS]),
         lambda rows: admin.table("clv_predictions").insert(rows, returning="minimal").execute())

    # 4. keep only the newest KEEP_RUNS runs
    res = admin.table("model_runs").select("predicted_at").order("predicted_at", desc=True).execute()
    runs = [r["predicted_at"] for r in cast(list[dict[str, Any]], res.data)]
    for old in runs[KEEP_RUNS:]:
        admin.table("clv_predictions").delete().eq("predicted_at", old).execute()
        admin.table("model_runs").delete().eq("predicted_at", old).execute()
        print(f"  removed old run {old}")

    # 5. dashboard snapshot → private bucket (one small file the app downloads instead of 121k rows)
    upload_snapshot(admin, df, run_at)

    # 6. model files → private bucket
    if not args.no_models:
        store = admin.storage.from_(BUCKET)
        for name in MODEL_FILES:
            path = ROOT / name
            store.upload(Path(name).name, path.read_bytes(),
                         {"content-type": "application/octet-stream", "upsert": "true"})
            print(f"  uploaded {Path(name).name} ({path.stat().st_size / 1e6:.1f} MB) to {BUCKET}")

    # 7. check
    count = admin.table("clv_predictions").select("prediction_id", count=CountMethod.exact).eq("predicted_at", run_at) \
        .limit(0).execute().count
    ok = count == len(df)
    print(f"{'PASS' if ok else 'FAIL'}  {count:,} predictions stored for this run (expected {len(df):,})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
