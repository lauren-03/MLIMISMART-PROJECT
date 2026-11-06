# Backing up the MlimiSmart database, and the deployment order

Everything in this file is for you to run. I have deliberately not run any
of it, because the backfill and the schema change both touch the live TiDB
database that the website depends on.

**Never paste the database password into a chat, an issue, a commit or a
screenshot.** Every command below reads it from your own machine, so the
password is never typed in the open.

---

## 1. Take the backup (do this first)

### Option A — TiDB Cloud's own backup (easiest, recommended)

1. Sign in at <https://tidbcloud.com>.
2. Open your cluster, then **Backup**.
3. Click **Backup Now** and name it `before-seasonal-backfill`.
4. Wait until its status reads **Succeeded**, and note the time it finished.

That is a full cluster snapshot, and it is what you restore from if anything
goes wrong.

### Option B — a local dump file as well

In PowerShell, set the connection details for this session only (replace the
values with your own from the TiDB Cloud connect dialog):

```powershell
$env:TIDB_HOST="<host>.tidbcloud.com"; $env:TIDB_PORT="4000"; $env:TIDB_USER="<user>"; $env:TIDB_DB="mlimismart"; $env:TIDB_PASSWORD=(Read-Host "TiDB password" -AsSecureString | ConvertFrom-SecureString -AsPlainText)
```

`Read-Host` keeps the password off your screen and out of your PowerShell
history. Then dump the database:

```powershell
mysqldump --host=$env:TIDB_HOST --port=$env:TIDB_PORT --user=$env:TIDB_USER --password=$env:TIDB_PASSWORD --ssl-mode=VERIFY_IDENTITY --single-transaction --set-gtid-purged=OFF $env:TIDB_DB > "$HOME\Documents\mlimismart-backup-$(Get-Date -Format yyyy-MM-dd).sql"
```

Check the file is not empty and ended properly:

```powershell
Get-Item "$HOME\Documents\mlimismart-backup-*.sql" | Select-Object Name,Length; Get-Content "$HOME\Documents\mlimismart-backup-*.sql" -Tail 3
```

A good dump is tens of megabytes (the weather history is large) and its last
line reads `-- Dump completed on ...`. If it is only a few kilobytes it
failed — stop and fix that before going further.

Close the terminal afterwards, so the password leaves memory.

---

## 2. Tell me the backup is done

I will not run the backfill or the migration until you confirm it. Your
supervisor asked for that explicitly, and it is the right rule.

---

## 3. Then, in this order

Each step is a **Render one-off job**: Render dashboard → your service →
**Jobs** → **New Job**, with the command below. Jobs get the same
environment variables and the same database as the website, and they do not
restart or interrupt it.

| # | Command | What it does | How long |
|---|---------|--------------|----------|
| 1 | `python migrate_model_storage.py --check` | Reports only. Confirms it can reach the database and changes nothing. | seconds |
| 2 | `python migrate_model_storage.py --apply` | Creates one new table, `model_artifacts`. Alters nothing that already exists. | seconds |
| 3 | `python backfill_history.py --from 2010-01-01 --check --report backfill.json` | Downloads the missing 2010–2015 weather and verifies coverage per area. | 10–30 min |
| 4 | `python train_seasonal.py --report seasonal_report.json` | Trains and evaluates the seasonal model on the real data. Saves it **unapproved**, so nothing changes for farmers yet. | 2–10 min |
| 5 | `python approve_model.py --list` | Shows the model and its real scores. **Read them before step 6.** | seconds |
| 6 | `python approve_model.py --model seasonal_rain --version 1 --approve` | Puts that model into service. Only if step 5's figures are defensible. | seconds |

Send me the output of steps 3, 4 and 5. Those are the real numbers. The
figures from my testing came from invented weather and must never appear in
your report.

---

## 4. Required environment variables

These already exist on Render. Placeholder names only — I have not read
their values and do not need them.

| Name | Holds |
|------|-------|
| `DATABASE_URL` | the full TiDB connection string, password included |
| `GEMINI_API_KEY` | the Google Gemini key |
| `AT_USERNAME`, `AT_API_KEY` | the Africa's Talking SMS and USSD credentials |
| `ALLOW_SQLITE_FALLBACK` | must be `false` in production, so a database outage fails loudly instead of quietly writing to a throwaway SQLite file |

---

## 5. If something goes wrong

| Problem | What to do |
|---------|-----------|
| The migration failed halfway | `python migrate_model_storage.py --rollback --yes`. It drops only `model_artifacts`. The site carries on with the models in `ml_store/`. |
| The backfill downloaded bad data | The backfill never deletes or overwrites, so the older rows are intact. Remove only the new range: `DELETE FROM weather_history WHERE day < '2016-01-01';` |
| The new seasonal model is poor | Do nothing. It is saved unapproved and is serving no one. |
| An approved model turns out to be wrong | `python approve_model.py --model seasonal_rain --version <older> --activate` goes back to the previous approved version. |
| The website itself breaks | Render dashboard → **Deploys** → the last successful deploy → **Rollback**. |

---

## 6. What "Stage 1 complete" will require

Not before all five of these:

1. The real backfill has run, and its verification report shows coverage per
   area with any gaps named.
2. Spatial correlation and effective sample size have been recomputed on the
   **real** weather, not my synthetic test data.
3. `train_seasonal.py` has produced genuine evaluation figures against the
   three baselines.
4. The model has been approved and shown to reload from the database after a
   deployment.
5. <https://mlimismart.onrender.com> has returned a real seasonal prediction,
   with the existing day-ahead advice still working.

Until then it is code that passes its tests, which is not the same thing.
