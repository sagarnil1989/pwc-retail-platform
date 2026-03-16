# Databricks notebook source
from pyspark.sql.functions import current_timestamp, lit, col
from typing import List, Dict

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

# --------------------------------------------------
# Helper: recursively list files under landing
# --------------------------------------------------
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

# --------------------------------------------------
# Helper: identify entity from file name
# --------------------------------------------------
def get_entity_config(file_name: str, entity_configs: List[Dict]) -> Dict:
    lower_name = file_name.lower()
    for cfg in entity_configs:
        if cfg["file_match_contains"] in lower_name:
            return cfg
    return None

# --------------------------------------------------
# Helper: extract batch folder from path
# Example:
# abfss://.../landing/day1/file.csv -> day1
# --------------------------------------------------
def get_snapshot_batch(file_path: str) -> str:
    path_after_landing = file_path.split("/landing/")[-1]
    path_parts = path_after_landing.split("/")
    if len(path_parts) > 1:
        return path_parts[0]
    return "unknown"

# --------------------------------------------------
# Main logic
# --------------------------------------------------
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
        print(f"Checking file: {file_path}")

        # --------------------------------------------------
        # Check if this exact file path was already loaded
        # Same filename in another folder = new file
        # --------------------------------------------------
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

        print(f"Processing file: {file_name} -> {cfg['target_table']}")

        snapshot_batch = get_snapshot_batch(file_path)

        # --------------------------------------------------
        # Read file
        # --------------------------------------------------
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

        # --------------------------------------------------
        # Write to bronze
        # --------------------------------------------------
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