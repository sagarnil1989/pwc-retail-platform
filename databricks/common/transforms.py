from typing import Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    to_date,
    row_number,
    coalesce,
    lit,
    sha2,
    concat_ws,
    sum as spark_sum,
    count as spark_count
)
from pyspark.sql.window import Window


# ----------------------------
# Bronze helpers
# ----------------------------
def get_entity_config(file_name: str, entity_configs: List[Dict]) -> Optional[Dict]:
    lower_name = file_name.lower()
    for cfg in entity_configs:
        if cfg["file_match_contains"] in lower_name:
            return cfg
    return None


def get_snapshot_batch(file_path: str) -> str:
    path_after_landing = file_path.split("/landing/")[-1]
    path_parts = path_after_landing.split("/")
    if len(path_parts) > 1:
        return path_parts[0]
    return "unknown"


# ----------------------------
# Silver transforms
# ----------------------------
def transform_customers(df: DataFrame) -> DataFrame:
    return (
        df.select(
            col("CustomerID"),
            col("FirstName"),
            col("LastName"),
            col("Gender"),
            to_date(col("BirthDate")).alias("BirthDate"),
            col("City"),
            to_date(col("JoinDate")).alias("JoinDate"),
            col("snapshot_batch"),
            col("ingestion_ts"),
            col("source_file_path"),
            col("source_file_name")
        )
    )


def transform_products(df: DataFrame) -> DataFrame:
    return (
        df.select(
            col("ProductID"),
            col("ProductName"),
            col("Category"),
            col("SubCategory"),
            col("UnitPrice").cast("double").alias("UnitPrice"),
            col("CostPrice").cast("double").alias("CostPrice"),
            col("snapshot_batch"),
            col("ingestion_ts"),
            col("source_file_path"),
            col("source_file_name")
        )
    )


def transform_stores(df: DataFrame) -> DataFrame:
    return (
        df.select(
            col("StoreID"),
            col("StoreName"),
            col("City"),
            col("Region"),
            col("snapshot_batch"),
            col("ingestion_ts"),
            col("source_file_path"),
            col("source_file_name")
        )
    )


def transform_transactions(df: DataFrame) -> DataFrame:
    return (
        df.select(
            col("TransactionID"),
            to_date(col("Date")).alias("Date"),
            col("CustomerID"),
            col("ProductID"),
            col("StoreID"),
            col("Quantity").cast("int").alias("Quantity"),
            col("Discount").cast("double").alias("Discount"),
            col("PaymentMethod"),
            col("snapshot_batch"),
            col("ingestion_ts"),
            col("source_file_path"),
            col("source_file_name")
        )
    )


def deduplicate_transactions(df: DataFrame) -> DataFrame:
    w = Window.partitionBy("TransactionID").orderBy(col("ingestion_ts").desc())
    return (
        df.withColumn("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("rn")
    )


def add_customer_hash(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "record_hash",
        sha2(
            concat_ws(
                "||",
                coalesce(col("FirstName").cast("string"), lit("")),
                coalesce(col("LastName").cast("string"), lit("")),
                coalesce(col("Gender").cast("string"), lit("")),
                coalesce(col("BirthDate").cast("string"), lit("")),
                coalesce(col("City").cast("string"), lit("")),
                coalesce(col("JoinDate").cast("string"), lit(""))
            ),
            256
        )
    )


def add_product_hash(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "record_hash",
        sha2(
            concat_ws(
                "||",
                coalesce(col("ProductName").cast("string"), lit("")),
                coalesce(col("Category").cast("string"), lit("")),
                coalesce(col("SubCategory").cast("string"), lit("")),
                coalesce(col("UnitPrice").cast("string"), lit("")),
                coalesce(col("CostPrice").cast("string"), lit(""))
            ),
            256
        )
    )


def add_store_hash(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "record_hash",
        sha2(
            concat_ws(
                "||",
                coalesce(col("StoreName").cast("string"), lit("")),
                coalesce(col("City").cast("string"), lit("")),
                coalesce(col("Region").cast("string"), lit(""))
            ),
            256
        )
    )


def deduplicate_by_key_and_hash(df: DataFrame, key_col: str) -> DataFrame:
    w = Window.partitionBy(key_col, "record_hash").orderBy(col("ingestion_ts").desc())
    return (
        df.withColumn("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("rn")
    )


# ----------------------------
# Gold transforms
# ----------------------------
def build_current_view(df: DataFrame) -> DataFrame:
    return df.filter(col("__END_AT").isNull())


def build_sales(transactions_df: DataFrame, products_df: DataFrame, stores_df: DataFrame) -> DataFrame:
    return (
        transactions_df.alias("t")
        .join(products_df.alias("p"), col("t.ProductID") == col("p.ProductID"), "left")
        .join(stores_df.alias("s"), col("t.StoreID") == col("s.StoreID"), "left")
        .select(
            col("t.TransactionID"),
            col("t.Date"),
            col("t.CustomerID"),
            col("t.ProductID"),
            col("t.StoreID"),
            col("s.Region"),
            col("t.Quantity"),
            col("p.UnitPrice"),
            col("t.Discount"),
            col("t.PaymentMethod"),
            (col("t.Quantity") * col("p.UnitPrice")).alias("GrossSalesAmount"),
            ((col("t.Quantity") * col("p.UnitPrice")) - coalesce(col("t.Discount"), lit(0.0))).alias("NetSalesAmount")
        )
    )


def build_region_highest_sales(sales_df: DataFrame) -> DataFrame:
    agg_df = (
        sales_df.groupBy("Date", "Region")
        .agg(spark_sum("NetSalesAmount").alias("TotalSales"))
    )

    w = Window.partitionBy("Date").orderBy(col("TotalSales").desc(), col("Region").asc())

    return (
        agg_df.withColumn("rn", row_number().over(w))
              .filter(col("rn") == 1)
              .drop("rn")
    )


def build_payment_preference(sales_df: DataFrame) -> DataFrame:
    agg_df = (
        sales_df.groupBy("Date", "Region", "PaymentMethod")
        .agg(
            spark_count("*").alias("PaymentCount"),
            spark_sum("NetSalesAmount").alias("TotalSales")
        )
    )

    w = Window.partitionBy("Date", "Region").orderBy(
        col("PaymentCount").desc(),
        col("TotalSales").desc(),
        col("PaymentMethod").asc()
    )

    return (
        agg_df.withColumn("rn", row_number().over(w))
              .filter(col("rn") == 1)
              .drop("rn")
    )