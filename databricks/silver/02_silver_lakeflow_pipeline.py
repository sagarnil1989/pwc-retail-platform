# Databricks notebook source

# COMMAND ----------

# Import necessary libraries and functions
from pyspark import pipelines as dp
from pyspark.sql.functions import col

from databricks.common.transforms import (
    transform_customers,
    transform_products,
    transform_stores,
    transform_transactions,
    deduplicate_transactions,
    add_customer_hash,
    add_product_hash,
    add_store_hash,
    deduplicate_by_key_and_hash
)

# COMMAND ----------

# Define the source table for customers with transformations and deduplication
@dp.table(name="customers_source")
def customers_source():
    df = spark.read.table("pwc_retail.bronze.customers_raw")
    df = transform_customers(df)
    df = add_customer_hash(df)
    df = deduplicate_by_key_and_hash(df, "CustomerID")
    return df

# COMMAND ----------

# Define the source table for products with transformations and deduplication
@dp.table(name="products_source")
def products_source():
    df = spark.read.table("pwc_retail.bronze.products_raw")
    df = transform_products(df)
    df = add_product_hash(df)
    df = deduplicate_by_key_and_hash(df, "ProductID")
    return df

# COMMAND ----------

# Define the source table for stores with transformations and deduplication
@dp.table(name="stores_source")
def stores_source():
    df = spark.read.table("pwc_retail.bronze.stores_raw")
    df = transform_stores(df)
    df = add_store_hash(df)
    df = deduplicate_by_key_and_hash(df, "StoreID")
    return df

# COMMAND ----------

# Define the transactions table with transformations and deduplication
@dp.table(name="transactions")
def transactions():
    df = spark.read.table("pwc_retail.bronze.transactions_raw")
    df = transform_transactions(df)
    df = deduplicate_transactions(df)
    return df

# COMMAND ----------

# Create target tables for SCD2 (Slowly Changing Dimension Type 2)
dp.create_target_table(name="customers_scd2")
dp.create_target_table(name="products_scd2")
dp.create_target_table(name="stores_scd2")

# COMMAND ----------

# Apply changes to customers_scd2 using SCD2 logic
dp.apply_changes(
    target="customers_scd2",
    source="customers_source",
    keys=["CustomerID"],
    sequence_by=col("ingestion_ts"),
    stored_as_scd_type="2",
    except_column_list=[
        "snapshot_batch",
        "ingestion_ts",
        "source_file_path",
        "source_file_name"
    ]
)

# COMMAND ----------

# Apply changes to products_scd2 using SCD2 logic
dp.apply_changes(
    target="products_scd2",
    source="products_source",
    keys=["ProductID"],
    sequence_by=col("ingestion_ts"),
    stored_as_scd_type="2",
    except_column_list=[
        "snapshot_batch",
        "ingestion_ts",
        "source_file_path",
        "source_file_name"
    ]
)

# COMMAND ----------

# Apply changes to stores_scd2 using SCD2 logic
dp.apply_changes(
    target="stores_scd2",
    source="stores_source",
    keys=["StoreID"],
    sequence_by=col("ingestion_ts"),
    stored_as_scd_type="2",
    except_column_list=[
        "snapshot_batch",
        "ingestion_ts",
        "source_file_path",
        "source_file_name"
    ]
)