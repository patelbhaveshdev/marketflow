# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Ingest Raw Trades
# MAGIC Lands raw OMS trade JSON drops into the bronze Delta layer.
# MAGIC Triggered by the MarketFlow orchestrator (`MF_INGEST_TRADES`).

# COMMAND ----------
from pyspark.sql import functions as F

RAW_PATH = "abfss://landing@marketflowsa.dfs.core.windows.net/oms/trades/"
BRONZE_TABLE = "marketflow.bronze_trades"

# --- No Azure? Use the committed sample data instead: ---
# 1. Generate/refresh it:  python tools/generate_sample_trades.py --count 500 --out data/sample/trades.json
# 2. Upload data/sample/*.json to DBFS (Catalog > Add data), then:
# RAW_PATH = "dbfs:/FileStore/marketflow/sample/"

# COMMAND ----------
raw = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", f"{RAW_PATH}_schema")
    .load(RAW_PATH)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

# COMMAND ----------
(
    raw.writeStream.format("delta")
    .option("checkpointLocation", f"{RAW_PATH}_checkpoint")
    .trigger(availableNow=True)  # batch semantics under scheduler control
    .toTable(BRONZE_TABLE)
)
