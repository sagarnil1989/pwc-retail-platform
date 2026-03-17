# Databricks notebook source

# COMMAND ----------

# Import necessary libraries and functions
from databricks.common.transforms import (
    build_current_view,
    build_sales,
    build_region_highest_sales,
    build_payment_preference
)

# COMMAND ----------

# Read SCD2 tables from Silver layer
products_scd2_df = spark.read.table("pwc_retail.silver.products_scd2")
stores_scd2_df = spark.read.table("pwc_retail.silver.stores_scd2")
customers_scd2_df = spark.read.table("pwc_retail.silver.customers_scd2")
transactions_df = spark.read.table("pwc_retail.silver.transactions")

# COMMAND ----------

# Build current views by filtering out ended records
products_current_df = build_current_view(products_scd2_df)
stores_current_df = build_current_view(stores_scd2_df)
customers_current_df = build_current_view(customers_scd2_df)

# COMMAND ----------

# Save current views to Silver layer tables
products_current_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("pwc_retail.silver.products_current")
stores_current_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("pwc_retail.silver.stores_current")
customers_current_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("pwc_retail.silver.customers_current")

# COMMAND ----------

# Build enriched sales fact table
sales_df = build_sales(transactions_df, products_current_df, stores_current_df)
sales_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("pwc_retail.gold.sales")

# COMMAND ----------

# Build table for daily region with highest sales
region_highest_sales_df = build_region_highest_sales(sales_df)
region_highest_sales_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("pwc_retail.gold.region_highest_sales")

# COMMAND ----------

# Build table for daily preferred payment method per region
payment_preference_df = build_payment_preference(sales_df)
payment_preference_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("pwc_retail.gold.payment_preference")