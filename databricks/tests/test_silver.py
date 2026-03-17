from databricks.common.transforms import get_entity_config, get_snapshot_batch


ENTITY_CONFIGS = [
    {
        "entity": "customers",
        "file_match_contains": "customer",
        "target_table": "pwc_retail.bronze.customers_raw"
    },
    {
        "entity": "products",
        "file_match_contains": "product",
        "target_table": "pwc_retail.bronze.products_raw"
    },
    {
        "entity": "stores",
        "file_match_contains": "store",
        "target_table": "pwc_retail.bronze.stores_raw"
    },
    {
        "entity": "transactions",
        "file_match_contains": "transaction",
        "target_table": "pwc_retail.bronze.transactions_raw"
    }
]


def test_get_entity_config_customers():
    cfg = get_entity_config("retail_sales_dataset_Customers.csv", ENTITY_CONFIGS)

    assert cfg is not None
    assert cfg["entity"] == "customers"
    assert cfg["target_table"] == "pwc_retail.bronze.customers_raw"


def test_get_entity_config_products_case_insensitive():
    cfg = get_entity_config("Retail_Sales_Dataset_PRODUCTS.csv", ENTITY_CONFIGS)

    assert cfg is not None
    assert cfg["entity"] == "products"


def test_get_entity_config_unknown_file_returns_none():
    cfg = get_entity_config("employee_master.csv", ENTITY_CONFIGS)

    assert cfg is None


def test_get_snapshot_batch_from_subfolder():
    file_path = "abfss://datalake@storage.dfs.core.windows.net/landing/day2/retail_sales_dataset_Customers.csv"

    assert get_snapshot_batch(file_path) == "day2"


def test_get_snapshot_batch_from_date_subfolder():
    file_path = "abfss://datalake@storage.dfs.core.windows.net/landing/2026-03-16/retail_sales_dataset_Stores.csv"

    assert get_snapshot_batch(file_path) == "2026-03-16"


def test_get_snapshot_batch_unknown_when_no_subfolder():
    file_path = "abfss://datalake@storage.dfs.core.windows.net/landing/retail_sales_dataset_Transactions.csv"

    assert get_snapshot_batch(file_path) == "unknown"