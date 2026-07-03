# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Ingest Raw Trades
# MAGIC Lands raw OMS trade JSON into the bronze Delta table.
# MAGIC Triggered by the MarketFlow orchestrator (`MF_INGEST_TRADES`).
# MAGIC
# MAGIC **Reproducible setup (no cloud keys required):** this notebook reads from a
# MAGIC Unity Catalog **Volume**, so it runs on Databricks Free/Serverless without
# MAGIC any storage credentials. One-time setup:
# MAGIC ```python
# MAGIC spark.sql("USE CATALOG <your_catalog>")          # e.g. main
# MAGIC spark.sql("CREATE SCHEMA IF NOT EXISTS marketflow")
# MAGIC spark.sql("CREATE VOLUME IF NOT EXISTS marketflow.landing")
# MAGIC # then Catalog UI -> marketflow.landing -> Upload data/sample/trades_*.json
# MAGIC ```
# MAGIC
# MAGIC **Production alternative (ADLS Gen2 + Auto Loader):** point `RAW_PATH` at
# MAGIC `abfss://landing@<account>.dfs.core.windows.net/oms/trades/` and use
# MAGIC `spark.readStream.format("cloudFiles")`. Supply the account key via a
# MAGIC Databricks secret scope - never hard-code it.

# COMMAND ----------
from pyspark.sql import functions as F

# Your workspace's catalog. Run `spark.sql("SHOW CATALOGS").show()` to find it.
CATALOG = "dbw_marketflow"
spark.sql(f"USE CATALOG {CATALOG}")

RAW_PATH = f"/Volumes/{CATALOG}/marketflow/landing/"
BRONZE_TABLE = "marketflow.bronze_trades"

# COMMAND ----------
raw = (
    spark.read.json(RAW_PATH)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

raw.write.mode("overwrite").saveAsTable(BRONZE_TABLE)
print("bronze rows:", spark.table(BRONZE_TABLE).count())
