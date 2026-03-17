-- Databricks notebook source
-- DBTITLE 1,Products Current View
-- Current dimension views from SCD2 outputs
CREATE OR REPLACE VIEW pwc_retail.silver.products_current AS
SELECT *
FROM pwc_retail.silver.products_scd2
WHERE __END_AT IS NULL;

-- COMMAND ----------

-- DBTITLE 1,Stores Current View
CREATE OR REPLACE VIEW pwc_retail.silver.stores_current AS
SELECT *
FROM pwc_retail.silver.stores_scd2
WHERE __END_AT IS NULL;

-- COMMAND ----------

-- DBTITLE 1,Customers Current View
CREATE OR REPLACE VIEW pwc_retail.silver.customers_current AS
SELECT *
FROM pwc_retail.silver.customers_scd2
WHERE __END_AT IS NULL;

-- COMMAND ----------

-- DBTITLE 1,Enriched Sales Fact
-- Enriched sales fact
CREATE OR REPLACE TABLE pwc_retail.gold.sales AS
SELECT
    t.TransactionID,
    t.Date,
    t.CustomerID,
    t.ProductID,
    t.StoreID,
    s.Region,
    t.Quantity,
    p.UnitPrice,
    t.Discount,
    t.PaymentMethod,
    (t.Quantity * p.UnitPrice) AS GrossSalesAmount,
    ((t.Quantity * p.UnitPrice) - COALESCE(t.Discount, 0)) AS NetSalesAmount
FROM pwc_retail.silver.transactions t
JOIN pwc_retail.silver.products_current p
    ON t.ProductID = p.ProductID
JOIN pwc_retail.silver.stores_current s
    ON t.StoreID = s.StoreID;

-- COMMAND ----------

-- DBTITLE 1,Region Highest Sales
-- Daily region with highest sales
CREATE OR REPLACE TABLE pwc_retail.gold.region_highest_sales AS
WITH region_sales AS (
    SELECT
        Date,
        Region,
        SUM(NetSalesAmount) AS TotalSales
    FROM pwc_retail.gold.sales
    GROUP BY Date, Region
),
ranked AS (
    SELECT
        Date,
        Region,
        TotalSales,
        DENSE_RANK() OVER (PARTITION BY Date ORDER BY TotalSales DESC) AS rnk
    FROM region_sales
)
SELECT
    Date,
    Region,
    TotalSales
FROM ranked
WHERE rnk = 1;

-- COMMAND ----------

-- DBTITLE 1,Payment Preference
-- Daily preferred payment method per region
CREATE OR REPLACE TABLE pwc_retail.gold.payment_preference AS
WITH payment_stats AS (
    SELECT
        Date,
        Region,
        PaymentMethod,
        COUNT(*) AS PaymentCount,
        SUM(NetSalesAmount) AS TotalSales
    FROM pwc_retail.gold.sales
    GROUP BY Date, Region, PaymentMethod
),
ranked AS (
    SELECT
        Date,
        Region,
        PaymentMethod,
        PaymentCount,
        TotalSales,
        ROW_NUMBER() OVER (
            PARTITION BY Date, Region
            ORDER BY PaymentCount DESC, TotalSales DESC, PaymentMethod
        ) AS rn
    FROM payment_stats
)
SELECT
    Date,
    Region,
    PaymentMethod,
    PaymentCount,
    TotalSales
FROM ranked
WHERE rn = 1;
