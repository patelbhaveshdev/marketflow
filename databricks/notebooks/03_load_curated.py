# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Load Curated
# MAGIC Silver -> gold Parquet (Unity Catalog Volume) + Azure SQL staging load.
# MAGIC After this notebook, the orchestrator calls `curated.usp_MergeTrades` to
# MAGIC MERGE staging into the curated table consumed by the REST API and reporting.
# MAGIC
# MAGIC **Credentials:** the SQL password below is a placeholder. In a real
# MAGIC workspace store it in a secret scope and read it with
# MAGIC `dbutils.secrets.get(scope="marketflow", key="sql-password")` - never
# MAGIC hard-code a password in a committed notebook.

# COMMAND ----------
# Your workspace's catalog (must match notebooks 01/02).
CATALOG = "dbw_marketflow"
spark.sql(f"USE CATALOG {CATALOG}")

SILVER_TABLE = "marketflow.silver_trades"
GOLD_PATH = f"/Volumes/{CATALOG}/marketflow/gold/trades_daily/"

SQL_HOST = "marketflow-sql-bp.database.windows.net"
SQL_DB = "marketflow"
SQL_USER = "bhavesh"
SQL_PASSWORD = "<your-sql-password>"  # use dbutils.secrets.get(...) in production

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
# Gold Parquet in a UC Volume (a Fabric OneLake shortcut can point here).
spark.sql("CREATE VOLUME IF NOT EXISTS marketflow.gold")
daily.write.mode("overwrite").partitionBy("trade_date").parquet(GOLD_PATH)

# COMMAND ----------
# Curated Azure SQL: load silver into the staging table.
# Requires "Allow Azure services and resources to access this server" on the
# Azure SQL server firewall so Databricks can connect.
(
    spark.table(SILVER_TABLE)
    .write.format("sqlserver")
    .option("host", SQL_HOST)
    .option("database", SQL_DB)
    .option("dbtable", "staging.Trades")
    .option("user", SQL_USER)
    .option("password", SQL_PASSWORD)
    .mode("overwrite")
    .save()
)

print("gold parquet + SQL staging load complete")

# COMMAND ----------
# MAGIC %md
# MAGIC Next, in SQL (SSMS or Azure Query editor):
# MAGIC ```sql
# MAGIC EXEC curated.usp_MergeTrades;
# MAGIC SELECT COUNT(*) FROM curated.Trades;                      -- expect 200
# MAGIC EXEC curated.usp_GetDailySummary @TradeDate = '2026-07-01';
# MAGIC ```
