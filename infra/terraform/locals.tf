locals {
  common_tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
    },
    var.tags
  )
  bronze_notebook_path = "/Workspace/Users/dasgupta.sagarnil@gmail.com/pwc-retail-platform/databricks/bronze/01_bronze_ingestion"
  silver_pipeline_path = "/Workspace/Users/dasgupta.sagarnil@gmail.com/pwc-retail-platform/databricks/silver/02_silver_lakeflow_pipeline"
  gold_notebook_path   = "/Workspace/Users/dasgupta.sagarnil@gmail.com/pwc-retail-platform/databricks/gold/03_gold_analytics.sql"
}