# Screenshots

Evidence that the pipeline was deployed and run on Azure. Referenced from the
main README's "Deployed & verified on Azure" section.

| File | Shows |
|------|-------|
| `2026-07-03_02.png` | `GET /api/jobs` on Azure App Service — migrated AutoSys jobs served live |
| `2026-07-03_03.png` | `GET /api/jobs` continued — job dependencies and priorities |

## Optional additions (for fuller visual proof)

Capture these while the Azure resources are still running, then add to the
README section:

- **Pipeline run** — `POST /api/pipeline/run` on Swagger, response showing every
  job `Succeeded` in dependency order (stronger than the empty `/api/runs`).
- **Databricks** — the notebook cell output `silver: 200`, `quarantine: 10`.
- **Azure SQL** — SSMS showing `EXEC curated.usp_GetDailySummary` results and
  `SELECT COUNT(*) FROM curated.Trades` = 200.

Capture on Windows with `Win + Shift + S`, save as PNG here, and reference them
in `../../README.md`.
