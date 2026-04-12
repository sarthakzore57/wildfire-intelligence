#!/usr/bin/env python
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(command: list[str], cwd: Path) -> None:
    print(f"Running: {' '.join(command)}")
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect dataset and retrain the global fire-risk model with versioning."
    )
    parser.add_argument(
        "--dataset-source",
        choices=["live", "bootstrap", "historical", "csv"],
        default="live",
        help="Dataset source to use before training.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1000,
        help="Number of samples for generated datasets (live/bootstrap).",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="training/data/global_live_dataset.csv",
        help="CSV dataset path relative to backend/ when --dataset-source=csv.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=20,
        help="Delay between live API calls in milliseconds when --dataset-source=live.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-01-01",
        help="Historical dataset start date in YYYY-MM-DD format when --dataset-source=historical.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2025-12-31",
        help="Historical dataset end date in YYYY-MM-DD format when --dataset-source=historical.",
    )
    parser.add_argument(
        "--event-limit",
        type=int,
        default=200,
        help="Max wildfire events to request when --dataset-source=historical.",
    )
    parser.add_argument(
        "--negatives-per-positive",
        type=int,
        default=1,
        help="Negative rows per positive row when --dataset-source=historical.",
    )
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parent.parent
    py = sys.executable

    if args.dataset_source == "live":
        dataset_path = "training/data/global_live_dataset.csv"
        _run(
            [
                py,
                "training/collect_live_global_dataset.py",
                "--samples",
                str(args.samples),
                "--seed",
                str(args.seed),
                "--output",
                dataset_path,
                "--sleep-ms",
                str(args.sleep_ms),
            ],
            cwd=backend_root,
        )
    elif args.dataset_source == "bootstrap":
        dataset_path = "training/data/global_bootstrap.csv"
        _run(
            [
                py,
                "training/bootstrap_dataset.py",
                "--samples",
                str(max(args.samples, 5000)),
                "--seed",
                str(args.seed),
                "--output",
                dataset_path,
            ],
            cwd=backend_root,
        )
    elif args.dataset_source == "historical":
        dataset_path = "training/data/historical_wildfire_dataset.csv"
        _run(
            [
                py,
                "training/build_historical_event_dataset.py",
                "--start-date",
                args.start_date,
                "--end-date",
                args.end_date,
                "--limit",
                str(args.event_limit),
                "--negatives-per-positive",
                str(args.negatives_per_positive),
                "--sleep-ms",
                str(args.sleep_ms),
                "--output",
                dataset_path,
                "--seed",
                str(args.seed),
            ],
            cwd=backend_root,
        )
    else:
        dataset_path = args.dataset_path

    _run(
        [
            py,
            "training/train_global_model.py",
            "--input",
            dataset_path,
            "--seed",
            str(args.seed),
            "--versioned",
        ],
        cwd=backend_root,
    )
    print("Retraining complete.")
    print("Latest model: app/models/trained/global_fire_risk_model.joblib")
    print("Registry: app/models/trained/model_registry.json")


if __name__ == "__main__":
    main()
