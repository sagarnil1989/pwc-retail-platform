variable "subscription_id" {
  type        = string
  description = "Azure subscription ID where infrastructure will be deployed."
}

variable "tenant_id" {
  type        = string
  description = "Azure Entra tenant ID used for authentication."
}

variable "client_id" {
  type        = string
  description = "Azure application or service principal client ID used for Azure authentication."
}
variable "client_secret" {
  type        = string
  description = "Azure application or service principal client secret used for Azure authentication."
  sensitive   = true
}

variable "location" {
  type        = string
  description = "Azure region where resources will be created."
}

variable "environment" {
  type        = string
  description = "Deployment environment name such as dev, test, or prod."
}

variable "project_name" {
  type        = string
  description = "Logical project name used for naming and tagging resources."
}

variable "resource_group_name" {
  type        = string
  description = "Name of the Azure resource group for the platform resources."
}

variable "databricks_workspace_name" {
  type        = string
  description = "Name of the Azure Databricks workspace."
}

variable "storage_account_name_prefix" {
  type        = string
  description = "Prefix used to generate the ADLS Gen2 storage account name."
}

variable "storage_filesystem_name" {
  type        = string
  description = "Name of the ADLS Gen2 filesystem or container."
}

variable "catalog_name" {
  type        = string
  description = "Unity Catalog catalog name for the retail platform."
}

variable "landing_schema_name" {
  type        = string
  description = "Schema name intended for landing-layer objects if used."
  default     = "landing"
}

variable "bronze_schema_name" {
  type        = string
  description = "Unity Catalog schema name for the bronze layer."
}

variable "silver_schema_name" {
  type        = string
  description = "Unity Catalog schema name for the silver layer."
}

variable "gold_schema_name" {
  type        = string
  description = "Unity Catalog schema name for the gold layer."
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to Azure and Databricks resources."
  default     = {}
}

variable "databricks_workspace_url" {
  type        = string
  description = "Workspace URL of the Azure Databricks workspace."
}

variable "databricks_pat" {
  type        = string
  description = "Databricks personal access token used by the Terraform Databricks provider."
  sensitive   = true
  default     = null
}

variable "databricks_principal" {
  type        = string
  description = "Databricks user, group, or service principal identifier used in permissions grants."
}

variable "workspace_project_root" {
  type        = string
  description = "Workspace root folder where notebooks are stored."
  default     = "/Workspace/Pwc_Assignment"
}

variable "pipeline_name" {
  type        = string
  description = "Name of the Databricks Lakeflow pipeline for the silver layer."
  default     = "pwc-retail-silver"
}

variable "job_name" {
  type        = string
  description = "Name of the Databricks job that orchestrates bronze, silver, and gold."
  default     = "Data Sync Pipeline Job"
}

variable "job_cron" {
  type        = string
  description = "Quartz cron expression for the Databricks scheduled job."
  default     = "0 0 5 * * ?"
}

variable "job_timezone" {
  type        = string
  description = "Timezone used by the Databricks scheduled job."
  default     = "Europe/Amsterdam"
}