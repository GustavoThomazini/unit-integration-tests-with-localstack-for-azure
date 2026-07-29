variable "location" {
  description = "Região do Azure onde os recursos serão provisionados"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Nome do ambiente (ex: dev, local, prod)"
  type        = string
  default     = "local"
}

variable "project_name" {
  description = "Nome base do projeto para padronização da nomenclatura dos recursos"
  type        = string
  default     = "secapp"
}

variable "vnet_address_space" {
  description = "Espaço de endereçamento da Virtual Network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "db_admin_username" {
  description = "Nome do administrador do SQL Server"
  type        = string
  default     = "sqladmin"
}

variable "localstack_secret" {
  description = "Secret fictício para bypass do LocalStack"
  type        = string
  default     = "localstack-dummy-secret"
  sensitive   = true
}