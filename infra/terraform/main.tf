data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
  numeric = true
}

# ------------------------------------------------------------------
# Resource Group
# ------------------------------------------------------------------
resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ------------------------------------------------------------------
# ADLS Gen2 Storage Account
# ------------------------------------------------------------------
resource "azurerm_storage_account" "adls" {
  name                     = substr(replace("${var.storage_account_name_prefix}${random_string.suffix.result}", "-", ""), 0, 24)
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  is_hns_enabled = true

  min_tls_version           = "TLS1_2"
  shared_access_key_enabled = true

  blob_properties {
    versioning_enabled = false
  }

  tags = local.common_tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "datalake" {
  name               = var.storage_filesystem_name
  storage_account_id = azurerm_storage_account.adls.id
}

# ------------------------------------------------------------------
# ADLS Directory Structure
# ------------------------------------------------------------------
resource "azurerm_storage_data_lake_gen2_path" "landing" {
  path               = "landing"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.datalake.name
  storage_account_id = azurerm_storage_account.adls.id
  resource           = "directory"
}

# ------------------------------------------------------------------
# Optional raw/checkpoints/artifacts external locations
# You can uncomment later once catalog is working
# ------------------------------------------------------------------
resource "databricks_external_location" "landing" {
  name            = "el-${var.project_name}-${var.environment}-landing"
  url             = "abfss://${azurerm_storage_data_lake_gen2_filesystem.datalake.name}@${azurerm_storage_account.adls.name}.dfs.core.windows.net/landing"
  credential_name = databricks_storage_credential.adls_sp.name
  comment         = "External location for landing files"
}


resource "azurerm_storage_data_lake_gen2_path" "checkpoints" {
  path               = "checkpoints"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.datalake.name
  storage_account_id = azurerm_storage_account.adls.id
  resource           = "directory"
}

resource "azurerm_storage_data_lake_gen2_path" "artifacts" {
  path               = "artifacts"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.datalake.name
  storage_account_id = azurerm_storage_account.adls.id
  resource           = "directory"
}

# ------------------------------------------------------------------
# ADLS path for Unity Catalog managed catalog storage
# ------------------------------------------------------------------
resource "azurerm_storage_data_lake_gen2_path" "catalogs_root" {
  path               = "catalogs"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.datalake.name
  storage_account_id = azurerm_storage_account.adls.id
  resource           = "directory"
}

resource "azurerm_storage_data_lake_gen2_path" "catalog_root" {
  path               = "catalogs/${var.catalog_name}"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.datalake.name
  storage_account_id = azurerm_storage_account.adls.id
  resource           = "directory"

  depends_on = [azurerm_storage_data_lake_gen2_path.catalogs_root]

  lifecycle {
    prevent_destroy = true
  }
}

# ------------------------------------------------------------------
# Role assignment so the service principal can read/write blob data
# Owner on subscription is management-plane heavy; blob data access
# should still be explicitly granted.
# ------------------------------------------------------------------
resource "azurerm_role_assignment" "sp_blob_data_contributor" {
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ------------------------------------------------------------------
# Azure Databricks Workspace
# ------------------------------------------------------------------
resource "azurerm_databricks_workspace" "this" {
  name                        = var.databricks_workspace_name
  resource_group_name         = azurerm_resource_group.this.name
  location                    = azurerm_resource_group.this.location
  sku                         = "premium"
  managed_resource_group_name = "${var.databricks_workspace_name}-managed-rg"

  tags = local.common_tags
}

# ------------------------------------------------------------------
# Storage credential using the same Azure service principal
# ------------------------------------------------------------------
resource "databricks_storage_credential" "adls_sp" {
  name    = "sc-${var.project_name}-${var.environment}"
  comment = "Storage credential for ADLS Gen2 using Azure service principal"

  azure_service_principal {
    directory_id   = var.tenant_id
    application_id = var.client_id
    client_secret  = var.client_secret
  }

  depends_on = [
    azurerm_role_assignment.sp_blob_data_contributor,
    azurerm_databricks_workspace.this
  ]
}

# ------------------------------------------------------------------
# External location for catalog managed storage
# ------------------------------------------------------------------
resource "databricks_external_location" "catalogs" {
  name            = "el-${var.project_name}-${var.environment}-catalogs"
  url             = "abfss://${azurerm_storage_data_lake_gen2_filesystem.datalake.name}@${azurerm_storage_account.adls.name}.dfs.core.windows.net/catalogs"
  credential_name = databricks_storage_credential.adls_sp.name
  comment         = "External location for Unity Catalog managed storage"

  depends_on = [
    databricks_storage_credential.adls_sp,
    azurerm_storage_data_lake_gen2_path.catalogs_root
  ]
}

# ------------------------------------------------------------------
# Grant permissions on external location
# IMPORTANT:
# var.databricks_principal should be the Databricks principal name
# such as user email, service principal display name, or group name.
# ------------------------------------------------------------------
resource "databricks_grants" "catalogs_external_location" {
  external_location = databricks_external_location.catalogs.name

  grant {
    principal = var.databricks_principal
    privileges = [
      "READ FILES",
      "WRITE FILES",
      "CREATE MANAGED STORAGE"
    ]
  }
}

# ------------------------------------------------------------------
# Unity Catalog objects
# ------------------------------------------------------------------
resource "databricks_catalog" "retail" {
  name         = var.catalog_name
  comment      = "PwC retail assignment catalog"
  storage_root = "abfss://${azurerm_storage_data_lake_gen2_filesystem.datalake.name}@${azurerm_storage_account.adls.name}.dfs.core.windows.net/catalogs/${var.catalog_name}"

  depends_on = [
    azurerm_databricks_workspace.this,
    azurerm_storage_data_lake_gen2_path.catalog_root,
    databricks_external_location.catalogs,
    databricks_grants.catalogs_external_location
  ]
}

resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.retail.name
  name         = var.bronze_schema_name
  comment      = "Bronze schema for raw Delta tables"

  depends_on = [databricks_catalog.retail]
}

resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.retail.name
  name         = var.silver_schema_name
  comment      = "Silver schema for conformed data"

  depends_on = [databricks_catalog.retail]
}

resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.retail.name
  name         = var.gold_schema_name
  comment      = "Gold schema for business outputs"

  depends_on = [databricks_catalog.retail]
}

# # ------------------------------------------------------------------
# # Add the Silver pipeline resource
# # ------------------------------------------------------------------
resource "databricks_pipeline" "silver" {
  name       = "pwc-retail-silver-tf"
  catalog    = var.catalog_name
  schema     = var.silver_schema_name
  serverless = true
  continuous = false

  library {
    notebook {
      path = local.silver_pipeline_path
    }
  }

  configuration = {
    env     = var.environment
    project = var.project_name
  }

  depends_on = [
    databricks_catalog.retail,
    databricks_schema.silver
  ]
}

# # ------------------------------------------------------------------
# # This keeps your Bronze → Silver → Gold flow with minimal change.
# # ------------------------------------------------------------------
resource "databricks_job" "data_sync_pipeline" {
  name = "Data Sync Pipeline Job TF "

  schedule {
    quartz_cron_expression = "0 0 5 ? * MON-FRI"
    timezone_id            = "Europe/Amsterdam"
    pause_status           = "UNPAUSED"
  }

  task {
    task_key = "Bronze"

    notebook_task {
      notebook_path = local.bronze_notebook_path
      source        = "WORKSPACE"
    }
  }

  task {
    task_key = "Silver"

    depends_on {
      task_key = "Bronze"
    }

    pipeline_task {
      pipeline_id  = databricks_pipeline.silver.id
      full_refresh = false
    }
  }

  task {
    task_key = "Gold"

    depends_on {
      task_key = "Silver"
    }

    notebook_task {
      notebook_path = local.gold_notebook_path
      source        = "WORKSPACE"
    }
  }

  tags = local.common_tags

  depends_on = [
    databricks_pipeline.silver
  ]
}

resource "databricks_permissions" "job_permissions" {
  job_id = databricks_job.data_sync_pipeline.id

  access_control {
    user_name        = var.databricks_principal
    permission_level = "CAN_MANAGE"
  }
}

resource "databricks_permissions" "pipeline_permissions" {
  pipeline_id = databricks_pipeline.silver.id

  access_control {
    user_name        = var.databricks_principal
    permission_level = "CAN_MANAGE"
  }
}