# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Load Curated
# MAGIC Silver -> Azure SQL curated layer consumed by reporting and the
# MAGIC MarketFlow REST API. Also lands gold Parquet in OneLake for
# MAGIC Microsoft Fabric semantic models (see /fabric).

# COMMAND ----------
SILVER_TABLE = "marketflow.silver_trades"
GOLD_PATH = "abfss://gold@marketflowsa.dfs.core.windows.net/trades_daily/"
SQL_URL = "jdbc:sqlserver://<your-server>.database.windows.net:1433;database=marketflow"

# COMMAND ----------
from pyspark.sql import functions as F

daily = (
    spark.table(SILVER_TABLE)
    .groupBy(F.to_date("executed_at").alias("trade_date"), "symbol", "desk", "side")
    .agg(
        F.count("*").alias("trade_count"),
        F.sum("quantity").alias("total_quantity"),
        F.sum("notional").alias("total_notional"),
        F.avg("price").alias("avg_price"),
    )
)

# COMMAND ----------
# Gold Parquet for Microsoft Fabric (OneLake shortcut points here)
daily.write.mode("overwrite").partitionBy("trade_date").parquet(GOLD_PATH)

# Curated Azure SQL for API/reporting (staging + MERGE via stored proc)
(
    spark.table(SILVER_TABLE)
    .write.format("jdbc")
    .option("url", SQL_URL)
    .option("dbtable", "staging.Trades")
    .option("authentication", "ActiveDirectoryMSI")
    .mode("overwrite")
    .save()
)

spark.sql("SELECT 1")  # placeholder: orchestrator invokes usp_MergeTrades next
