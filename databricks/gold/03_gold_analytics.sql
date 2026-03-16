# Databricks notebook source

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Databricks SQL
# MAGIC 
# MAGIC -- Current dimension views from SCD2 outputs
# MAGIC CREATE OR REPLACE VIEW pwc_retail.silver.products_current AS
# MAGIC SELECT *
# MAGIC FROM pwc_retail.silver.products_scd2
# MAGIC WHERE __END_AT IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW pwc_retail.silver.stores_current AS
# MAGIC SELECT *
# MAGIC FROM pwc_retail.silver.stores_scd2
# MAGIC WHERE __END_AT IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW pwc_retail.silver.customers_current AS
# MAGIC SELECT *
# MAGIC FROM pwc_retail.silver.customers_scd2
# MAGIC WHERE __END_AT IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Enriched sales fact
# MAGIC CREATE OR REPLACE TABLE pwc_retail.gold.sales AS
# MAGIC SELECT
# MAGIC     t.TransactionID,
# MAGIC     t.Date,
# MAGIC     t.CustomerID,
# MAGIC     t.ProductID,
# MAGIC     t.StoreID,
# MAGIC     s.Region,
# MAGIC     t.Quantity,
# MAGIC     p.UnitPrice,
# MAGIC     t.Discount,
# MAGIC     t.PaymentMethod,
# MAGIC     (t.Quantity * p.UnitPrice) AS GrossSalesAmount,
# MAGIC     ((t.Quantity * p.UnitPrice) - COALESCE(t.Discount, 0)) AS NetSalesAmount
# MAGIC FROM pwc_retail.silver.transactions t
# MAGIC JOIN pwc_retail.silver.products_current p
# MAGIC     ON t.ProductID = p.ProductID
# MAGIC JOIN pwc_retail.silver.stores_current s
# MAGIC     ON t.StoreID = s.StoreID;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Daily region with highest sales
# MAGIC CREATE OR REPLACE TABLE pwc_retail.gold.region_highest_sales AS
# MAGIC WITH region_sales AS (
# MAGIC     SELECT
# MAGIC         Date,
# MAGIC         Region,
# MAGIC         SUM(NetSalesAmount) AS TotalSales
# MAGIC     FROM pwc_retail.gold.sales
# MAGIC     GROUP BY Date, Region
# MAGIC ),
# MAGIC ranked AS (
# MAGIC     SELECT
# MAGIC         Date,
# MAGIC         Region,
# MAGIC         TotalSales,
# MAGIC         DENSE_RANK() OVER (PARTITION BY Date ORDER BY TotalSales DESC) AS rnk
# MAGIC     FROM region_sales
# MAGIC )
# MAGIC SELECT
# MAGIC     Date,
# MAGIC     Region,
# MAGIC     TotalSales
# MAGIC FROM ranked
# MAGIC WHERE rnk = 1;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Daily preferred payment method per region
# MAGIC CREATE OR REPLACE TABLE pwc_retail.gold.payment_preference AS
# MAGIC WITH payment_stats AS (
# MAGIC     SELECT
# MAGIC         Date,
# MAGIC         Region,
# MAGIC         PaymentMethod,
# MAGIC         COUNT(*) AS PaymentCount,
# MAGIC         SUM(NetSalesAmount) AS TotalSales
# MAGIC     FROM pwc_retail.gold.sales
# MAGIC     GROUP BY Date, Region, PaymentMethod
# MAGIC ),
# MAGIC ranked AS (
# MAGIC     SELECT
# MAGIC         Date,
# MAGIC         Region,
# MAGIC         PaymentMethod,
# MAGIC         PaymentCount,
# MAGIC         TotalSales,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY Date, Region
# MAGIC             ORDER BY PaymentCount DESC, TotalSales DESC, PaymentMethod
# MAGIC         ) AS rn
# MAGIC     FROM payment_stats
# MAGIC )
# MAGIC SELECT
# MAGIC     Date,
# MAGIC     Region,
# MAGIC     PaymentMethod,
# MAGIC     PaymentCount,
# MAGIC     TotalSales
# MAGIC FROM ranked
# MAGIC WHERE rn = 1;