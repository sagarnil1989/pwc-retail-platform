variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
  sensitive   = true
}

variable "tenant_id" {
  type        = string
  description = "Azure tenant ID"
  sensitive   = true
}

variable "client_id" {
  type        = string
  description = "Service principal client ID"
  sensitive   = true
}

variable "client_secret" {
  type        = string
  description = "Service principal client secret"
  sensitive   = true
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "westeurope"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "dev"
}

variable "project_name" {
  type        = string
  description = "Project short name"
  default     = "pwc-retail"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
  default     = "rg-pwc-retail-dev"
}

variable "databricks_workspace_name" {
  type        = string
  description = "Azure Databricks workspace name"
  default     = "adb-pwc-retail-dev"
}

variable "storage_account_name_prefix" {
  type        = string
  description = "Prefix for storage account name. Must be lowercase and short."
  default     = "stpwcretail"
}

variable "catalog_name" {
  type        = string
  description = "Unity Catalog catalog name"
  default     = "pwc_retail"
}

variable "landing_schema_name" {
  type        = string
  default     = "landing"
}

variable "bronze_schema_name" {
  type        = string
  default     = "bronze"
}

variable "silver_schema_name" {
  type        = string
  default     = "silver"
}

variable "gold_schema_name" {
  type        = string
  default     = "gold"
}

variable "storage_filesystem_name" {
  type        = string
  description = "ADLS Gen2 filesystem/container name"
  default     = "datalake"
}

variable "tags" {
  type        = map(string)
  default     = {}
}

variable "databricks_workspace_url" {
  type        = string
  description = "Databricks workspace URL (e.g. https://adb-1234567890123456.1.azuredatabricks.net)"
}

variable "databricks_principal" {
  type        = string
  description = "Databricks principal name that will receive external location grants. Example: your user email or Databricks service principal display name."
}

variable "databricks_pat" {
  type      = string
  sensitive = true
}