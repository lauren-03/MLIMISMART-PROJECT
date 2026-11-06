# -*- coding: utf-8 -*-
"""List, approve, activate or roll back the stored models.

A model saved by a training job is not used by the website until it is
approved here. This is the control that stops a bad training run from
replacing the model farmers are relying on.

    python approve_model.py --list
    python approve_model.py --model seasonal_rain --version 1 --show
    python approve_model.py --model seasonal_rain --version 1 --approve
    python approve_model.py --model seasonal_rain --version 1 --activate
"""
from __future__ import annotations

import argparse
import json


def main() -> int:
    ap = argparse.ArgumentParser(description="Approve or roll back a trained model.")
    ap.add_argument("--list", action="store_true", help="show the stored models")
    ap.add_argument("--model", help="model name, e.g. seasonal_rain")
    ap.add_argument("--version", type=int, help="model version")
    ap.add_argument("--show", action="store_true", help="print this version's full report")
    ap.add_argument("--approve", action="store_true",
                    help="mark this version fit for service and make it active")
    ap.add_argument("--activate", action="store_true",
                    help="serve this already-approved version (use to roll back)")
    ap.add_argument("--by", default="project supervisor", help="who approved it")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.ml import store
    from app.models import ModelArtifact
    from sqlalchemy import select

    db = SessionLocal()
    try:
        if args.list or not args.model:
            rows = store.artifacts(db, args.model)
            if not rows:
                print("No models are stored in the database yet.")
                return 0
            for r in rows:
                flag = "ACTIVE " if r["active"] else ("approved" if r["approved"]
                                                      else "UNAPPROVED")
                print(f"{r['model_name']:<16} v{r['version']:<4} {flag:<11}"
                      f"{r['dataset_version']:<28} {r['train_rows']:>6} rows  "
                      f"{r['size_bytes'] / 1024:.0f} KB  {r['trained_at']}")
                if r["metrics"]:
                    print(f"{'':>18}{json.dumps(r['metrics'])}")
            return 0

        if not args.version:
            print("Give --version as well.")
            return 2

        row = db.scalar(select(ModelArtifact).where(
            ModelArtifact.model_name == args.model,
            ModelArtifact.version == args.version))
        if row is None:
            print(f"{args.model} v{args.version} is not stored.")
            return 2

        if args.show:
            print(row.report or row.metrics or "(no report stored)")
            return 0

        if args.approve:
            store.approve(db, args.model, args.version, by=args.by)
            print(f"{args.model} v{args.version} approved and active.")
            return 0

        if args.activate:
            if store.activate(db, args.model, args.version):
                print(f"{args.model} v{args.version} is now the active model.")
                return 0
            print("That version is not approved, so it cannot be activated.")
            return 2

        print(f"{args.model} v{args.version}: approved={row.approved} "
              f"active={row.active} dataset={row.dataset_version}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
