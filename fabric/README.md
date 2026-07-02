# Microsoft Fabric Layer

The gold Parquet output from `databricks/notebooks/03_load_curated.py` lands in
ADLS Gen2 (`gold/trades_daily/`). Fabric consumes it without copying data:

1. **OneLake shortcut** – in a Fabric Lakehouse, create a shortcut to the
   `gold` container so `trades_daily` appears as a Lakehouse table.
2. **Data pipeline** – `pipeline_trades_refresh.json` (Fabric Data Factory
   pipeline) refreshes the semantic model after the MarketFlow orchestrator
   reports a successful `MF_LOAD_CURATED` run (webhook -> Fabric REST API).
3. **Semantic model** – star schema over `trades_daily` with measures:
   `Total Notional`, `Trade Count`, `Avg Price`, and time intelligence on
   `trade_date`.
4. **Report** – a Power BI report ("Trading Activity Daily") sits on the
   semantic model; desks slice by symbol, side and desk.

```
Databricks (gold Parquet) ──OneLake shortcut──> Fabric Lakehouse
                                   │
                                   └─> Semantic model ──> Power BI report
```
