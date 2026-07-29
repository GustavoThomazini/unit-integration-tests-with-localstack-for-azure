output "resource_group_name" {
  description = "Nome do Resource Group criado"
  value       = azurerm_resource_group.rg.name
}

output "webapp_url" {
  description = "URL de acesso da aplicação Web"
  value       = "https://${azurerm_linux_web_app.webapp.default_hostname}"
}

output "keyvault_uri" {
  description = "URI do Key Vault (utilizado pela aplicação para buscar segredos)"
  value       = azurerm_key_vault.kv.vault_uri
}

output "sql_server_fqdn" {
  description = "Fully Qualified Domain Name (FQDN) do SQL Server"
  value       = azurerm_mssql_server.sql_server.fully_qualified_domain_name
}

output "app_identity_client_id" {
  description = "Client ID da Identidade Gerenciada da Aplicação"
  value       = azurerm_user_assigned_identity.app_identity.client_id
}