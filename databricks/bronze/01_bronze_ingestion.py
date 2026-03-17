# Databricks notebook source
from pyspark.sql.functions import current_timestamp, lit, col
from typing import List, Dict

from databricks.common.transforms import get_entity_config, get_snapshot_batch

# --------------------------------------------------
# Config
# --------------------------------------------------
storage_account = "stpwcretailzeh5o"
container = "datalake"
catalog = "pwc_retail"
bronze_schema = "bronze"

base_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net"
landing_base_path = f"{base_path}/landing"

entity_configs = [
    {
        "entity": "customers",
        "file_match_contains": "customer",
        "target_table": f"{catalog}.{bronze_schema}.customers_raw"
    },
    {
        "entity": "products",
        "file_match_contains": "product",
        "target_table": f"{catalog}.{bronze_schema}.products_raw"
    },
    {
        "entity": "stores",
        "file_match_contains": "store",
        "target_table": f"{catalog}.{bronze_schema}.stores_raw"
    },
    {
        "entity": "transactions",
        "file_match_contains": "transaction",
        "target_table": f"{catalog}.{bronze_schema}.transactions_raw"
    }
]

def list_files_recursive(path: str) -> List[Dict]:
    results = []
    for item in dbutils.fs.ls(path):
        if item.isDir():
            results.extend(list_files_recursive(item.path))
        else:
            results.append({
                "path": item.path,
                "name": item.name
            })
    return results

all_files = list_files_recursive(landing_base_path)

if not all_files:
    print("No files found in landing.")
else:
    print(f"Found {len(all_files)} file(s) in landing.")

for file_meta in all_files:
    file_path = file_meta["path"]
    file_name = file_meta["name"]

    cfg = get_entity_config(file_name, entity_configs)

    if cfg is None:
        print(f"Skipping unmatched file: {file_name}")
        continue

    try:
        already_loaded = False

        if spark.catalog.tableExists(cfg["target_table"]):
            already_loaded = (
                spark.table(cfg["target_table"])
                .filter(col("source_file_path") == file_path)
                .limit(1)
                .count() > 0
            )

        if already_loaded:
            print(f"Skipping already loaded file path: {file_path}")
            continue

        snapshot_batch = get_snapshot_batch(file_path)

        df = (
            spark.read
            .option("header", True)
            .csv(file_path)
            .withColumn("source_file_path", lit(file_path))
            .withColumn("source_file_name", lit(file_name))
            .withColumn("snapshot_batch", lit(snapshot_batch))
            .withColumn("ingestion_ts", current_timestamp())
            .withColumn("entity_name", lit(cfg["entity"]))
        )

        if df.limit(1).count() > 0:
            (
                df.write
                .format("delta")
                .mode("append")
                .option("mergeSchema", "true")
                .saveAsTable(cfg["target_table"])
            )
            print(f"Loaded file into {cfg['target_table']}: {file_path}")
        else:
            print(f"File is empty, skipping load: {file_path}")

    except Exception as e:
        print(f"ERROR processing file {file_path}: {str(e)}")