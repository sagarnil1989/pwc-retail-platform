from pyspark.sql import Row

from databricks.common.transforms import (
    build_current_view,
    build_sales,
    build_region_highest_sales,
    build_payment_preference,
)


def test_build_current_view_filters_active_records(spark):
    df = spark.createDataFrame([
        Row(ProductID="P1", ProductName="Laptop", __END_AT=None),
        Row(ProductID="P2", ProductName="Mouse", __END_AT="2026-03-15 00:00:00"),
    ])

    result = build_current_view(df).collect()

    assert len(result) == 1
    assert result[0]["ProductID"] == "P1"


def test_build_sales_calculates_gross_and_net_sales(spark):
    transactions_df = spark.createDataFrame([
        Row(
            TransactionID="T1",
            Date="2026-03-15",
            CustomerID="C1",
            ProductID="P1",
            StoreID="S1",
            Quantity=2,
            Discount=3.0,
            PaymentMethod="Card",
        )
    ])

    products_df = spark.createDataFrame([
        Row(ProductID="P1", UnitPrice=10.0)
    ])

    stores_df = spark.createDataFrame([
        Row(StoreID="S1", Region="West")
    ])

    result = build_sales(transactions_df, products_df, stores_df).collect()[0]

    assert result["TransactionID"] == "T1"
    assert result["Region"] == "West"
    assert result["GrossSalesAmount"] == 20.0
    assert result["NetSalesAmount"] == 17.0


def test_build_sales_handles_null_discount(spark):
    transactions_df = spark.createDataFrame([
        Row(
            TransactionID="T2",
            Date="2026-03-15",
            CustomerID="C2",
            ProductID="P2",
            StoreID="S2",
            Quantity=3,
            Discount=None,
            PaymentMethod="Cash",
        )
    ])

    products_df = spark.createDataFrame([
        Row(ProductID="P2", UnitPrice=5.0)
    ])

    stores_df = spark.createDataFrame([
        Row(StoreID="S2", Region="East")
    ])

    result = build_sales(transactions_df, products_df, stores_df).collect()[0]

    assert result["GrossSalesAmount"] == 15.0
    assert result["NetSalesAmount"] == 15.0


def test_build_region_highest_sales_returns_top_region_per_day(spark):
    sales_df = spark.createDataFrame([
        Row(Date="2026-03-15", Region="West", NetSalesAmount=30.0, PaymentMethod="Card"),
        Row(Date="2026-03-15", Region="East", NetSalesAmount=50.0, PaymentMethod="Cash"),
        Row(Date="2026-03-16", Region="North", NetSalesAmount=20.0, PaymentMethod="Card"),
        Row(Date="2026-03-16", Region="South", NetSalesAmount=10.0, PaymentMethod="Cash"),
    ])

    result = build_region_highest_sales(sales_df).orderBy("Date").collect()

    assert len(result) == 2
    assert result[0]["Date"] == "2026-03-15"
    assert result[0]["Region"] == "East"
    assert result[0]["TotalSales"] == 50.0
    assert result[1]["Date"] == "2026-03-16"
    assert result[1]["Region"] == "North"
    assert result[1]["TotalSales"] == 20.0


def test_build_region_highest_sales_tie_breaks_by_region_name(spark):
    sales_df = spark.createDataFrame([
        Row(Date="2026-03-15", Region="East", NetSalesAmount=50.0, PaymentMethod="Card"),
        Row(Date="2026-03-15", Region="West", NetSalesAmount=50.0, PaymentMethod="Cash"),
    ])

    result = build_region_highest_sales(sales_df).collect()

    assert len(result) == 1
    assert result[0]["Region"] == "East"


def test_build_payment_preference_uses_count_then_sales_then_name(spark):
    sales_df = spark.createDataFrame([
        Row(Date="2026-03-15", Region="West", PaymentMethod="Card", NetSalesAmount=20.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Card", NetSalesAmount=10.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Cash", NetSalesAmount=40.0),
    ])

    result = build_payment_preference(sales_df).collect()

    assert len(result) == 1
    assert result[0]["Date"] == "2026-03-15"
    assert result[0]["Region"] == "West"
    assert result[0]["PaymentMethod"] == "Card"
    assert result[0]["PaymentCount"] == 2
    assert result[0]["TotalSales"] == 30.0


def test_build_payment_preference_tie_breaks_by_total_sales(spark):
    sales_df = spark.createDataFrame([
        Row(Date="2026-03-15", Region="West", PaymentMethod="Card", NetSalesAmount=20.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Card", NetSalesAmount=10.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Cash", NetSalesAmount=25.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Cash", NetSalesAmount=10.0),
    ])

    result = build_payment_preference(sales_df).collect()

    assert len(result) == 1
    assert result[0]["PaymentMethod"] == "Cash"
    assert result[0]["PaymentCount"] == 2
    assert result[0]["TotalSales"] == 35.0


def test_build_payment_preference_final_tie_breaks_by_payment_method_name(spark):
    sales_df = spark.createDataFrame([
        Row(Date="2026-03-15", Region="West", PaymentMethod="Card", NetSalesAmount=20.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Card", NetSalesAmount=10.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Cash", NetSalesAmount=15.0),
        Row(Date="2026-03-15", Region="West", PaymentMethod="Cash", NetSalesAmount=15.0),
    ])

    result = build_payment_preference(sales_df).collect()

    assert len(result) == 1
    assert result[0]["PaymentMethod"] == "Card"