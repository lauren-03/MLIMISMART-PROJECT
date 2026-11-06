# -*- coding: utf-8 -*-
"""Create the model_artifacts table, and nothing else.

    python migrate_model_storage.py --check      # report only, change nothing
    python migrate_model_storage.py --apply      # create the table
    python migrate_model_storage.py --rollback   # drop the table

Why this is safe to run on the live database
--------------------------------------------
It only ever CREATEs or DROPs one new table, model_artifacts. No existing
table is altered and no existing row is read or written, so the weather
history, the farmers, the advice records and model_runs are untouched.
That is also why the rollback is a clean DROP: nothing else points at it.

Take the database backup first anyway. The instructions are in
docs/DATABASE_BACKUP.md.
"""
from __future__ import annotations

import argparse

TABLE = "model_artifacts"


def main() -> int:
    ap = argparse.ArgumentParser(description="Create or drop the model_artifacts table.")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="report, change nothing")
    group.add_argument("--apply", action="store_true", help="create the table")
    group.add_argument("--rollback", action="store_true", help="drop the table")
    ap.add_argument("--yes", action="store_true", help="skip the rollback confirmation")
    args = ap.parse_args()

    from sqlalchemy import inspect, select, func
    from app.database import engine, SessionLocal, active_database_url
    from app.models import ModelArtifact

    # Never print the whole URL: it carries the password.
    where = active_database_url.split("@")[-1]
    print(f"Database: {where}")

    inspector = inspect(engine)
    exists = TABLE in inspector.get_table_names()
    print(f"Table {TABLE}: {'present' if exists else 'absent'}")

    if args.check:
        if exists:
            db = SessionLocal()
            try:
                total = db.scalar(select(func.count()).select_from(ModelArtifact))
                approved = db.scalar(select(func.count()).select_from(ModelArtifact)
                                     .where(ModelArtifact.approved.is_(True)))
                print(f"Rows: {total} stored, {approved} approved")
            finally:
                db.close()
        print(f"Other tables are untouched by this script: "
              f"{len(inspector.get_table_names())} tables in the database.")
        return 0

    if args.apply:
        if exists:
            print("Nothing to do.")
            return 0
        ModelArtifact.__table__.create(bind=engine)
        print(f"Created {TABLE}.")
        return 0

    if args.rollback:
        if not exists:
            print("Nothing to drop.")
            return 0
        db = SessionLocal()
        try:
            total = db.scalar(select(func.count()).select_from(ModelArtifact))
        finally:
            db.close()
        print(f"This will drop {TABLE} and the {total} stored model(s) in it. "
              "The models on disk and the model_runs history are not affected.")
        if not args.yes:
            if input("Type 'drop' to continue: ").strip().lower() != "drop":
                print("Cancelled.")
                return 1
        ModelArtifact.__table__.drop(bind=engine)
        print(f"Dropped {TABLE}. The backend falls back to the models in ml_store/.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
