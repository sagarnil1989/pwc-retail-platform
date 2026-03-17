terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }

    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.111.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-tf-state"
    storage_account_name = "stterraformstatepwc"
    container_name       = "tfstate"
    key                  = "pwc-retail-dev.tfstate"
    tenant_id            = "b82fab88-2f13-4992-a425-5bf3069f8df2"
    subscription_id      = "82710df5-bd00-45bb-801d-537e387dface"
    client_id            = "0a25767b-4e60-4b84-9864-c3c541887736"
  }
}

provider "azurerm" {
  features {}

  # optional if you use service principal vars / env vars
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

provider "databricks" {
  host  = var.databricks_workspace_url
  token = var.databricks_pat
}