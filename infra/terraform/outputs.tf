# output "resource_group_name" {
#   value = azurerm_resource_group.this.name
# }

# output "storage_account_name" {
#   value = azurerm_storage_account.adls.name
# }

# output "filesystem_name" {
#   value = azurerm_storage_data_lake_gen2_filesystem.datalake.name
# }

# output "databricks_workspace_name" {
#   value = azurerm_databricks_workspace.this.name
# }

# output "databricks_workspace_id" {
#   value = azurerm_databricks_workspace.this.id
# }

# output "catalog_name" {
#   value = databricks_catalog.retail.name
# }

# output "raw_external_location_url" {
#   value = databricks_external_location.raw.url
# }

# output "checkpoints_external_location_url" {
#   value = databricks_external_location.checkpoints.url
# }

# output "artifacts_external_location_url" {
#   value = databricks_external_location.artifacts.url
# }

# output "raw_volume_path_hint" {
#   value = "/Volumes/${databricks_catalog.retail.name}/${databricks_schema.landing.name}/${databricks_volume.raw_files.name}"
# }

# output "checkpoints_volume_path_hint" {
#   value = "/Volumes/${databricks_catalog.retail.name}/${databricks_schema.landing.name}/${databricks_volume.checkpoints.name}"
# }

# output "artifacts_volume_path_hint" {
#   value = "/Volumes/${databricks_catalog.retail.name}/${databricks_schema.landing.name}/${databricks_volume.artifacts.name}"
# }