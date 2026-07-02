# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Transform Trades
# MAGIC Bronze -> Silver: normalize, dedupe on trade_id (latest version wins),
# MAGIC enrich with instrument reference data, quarantine bad records.

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.window import Window

BRONZE_TABLE = "marketflow.bronze_trades"
SILVER_TABLE = "marketflow.silver_trades"
QUARANTINE_TABLE = "marketflow.quarantine_trades"

# COMMAND ----------
bronze = spark.table(BRONZE_TABLE)

typed = (
    bronze.select(
        F.col("trade_id").cast("string"),
        F.col("version").cast("int"),
        F.col("symbol").cast("string"),
        F.upper("side").alias("side"),
        F.col("quantity").cast("decimal(18,4)"),
        F.col("price").cast("decimal(18,6)"),
        F.to_timestamp("executed_at").alias("executed_at"),
        F.col("desk").cast("string"),
        F.col("_ingested_at"),
    )
)

# COMMAND ----------
valid_filter = (
    F.col("trade_id").isNotNull()
    & F.col("executed_at").isNotNull()
    & (F.col("quantity") > 0)
    & (F.col("price") > 0)
    & F.col("side").isin("BUY", "SELL")
)

typed.filter(~valid_filter).write.mode("append").saveAsTable(QUARANTINE_TABLE)

latest = Window.partitionBy("trade_id").orderBy(F.col("version").desc())
silver = (
    typed.filter(valid_filter)
    .withColumn("_rn", F.row_number().over(latest))
    .filter("_rn = 1")
    .drop("_rn")
    .withColumn("notional", F.col("quantity") * F.col("price"))
)

silver.write.mode("overwrite").saveAsTable(SILVER_TABLE)
print(f"silver rows: {spark.table(SILVER_TABLE).count()}")
