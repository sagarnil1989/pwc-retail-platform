from pyspark import pipelines as dp
from pyspark.sql.functions import col, to_date, row_number
from pyspark.sql.window import Window

@dp.table(name="customers_source")
def customers_source():
    return (
        spark.read.table("pwc_retail.bronze.customers_raw")
        .select(
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

@dp.table(name="products_source")
def products_source():
    return (
        spark.read.table("pwc_retail.bronze.products_raw")
        .select(
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

@dp.table(name="stores_source")
def stores_source():
    return (
        spark.read.table("pwc_retail.bronze.stores_raw")
        .select(
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

@dp.table(name="transactions")
def transactions():
    src = (
        spark.read.table("pwc_retail.bronze.transactions_raw")
        .select(
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

    w = Window.partitionBy("TransactionID").orderBy(col("ingestion_ts").desc())
    return (
        src.withColumn("rn", row_number().over(w))
           .filter(col("rn") == 1)
           .drop("rn")
    )

# SCD2 targets as regular pipeline tables
dp.create_target_table(name="customers_scd2")
dp.create_target_table(name="products_scd2")
dp.create_target_table(name="stores_scd2")

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