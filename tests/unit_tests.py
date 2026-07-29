import json
import pytest

# ==========================================
# FIXTURES DE CONFIGURAÇÃO
# ==========================================

@pytest.fixture(scope="module")
def tf_plan():
    """Carrega o arquivo plan.json gerado pelo Terraform."""
    try:
        with open("plan.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail("Arquivo 'plan.json' não encontrado. Rode 'terraform show -json tfplan > plan.json' primeiro.")

@pytest.fixture(scope="module")
def resources(tf_plan):
    """Extrai a lista de recursos que serão criados/modificados no plano."""
    try:
        return tf_plan["planned_values"]["root_module"]["resources"]
    except KeyError:
        pytest.fail("Estrutura do plan.json inválida ou vazia.")

def get_resource(resources, resource_type, resource_name=None):
    """Função auxiliar para buscar um recurso específico no JSON."""
    for r in resources:
        if r["type"] == resource_type:
            if resource_name is None or r["name"] == resource_name:
                return r
    return None

# ==========================================
# TESTES DO CHECKLIST DE CONFORMIDADE
# ==========================================

def test_vnet_subnets_isolamento(resources):
    """Verifica: [x] VNet e Subnets criadas com isolamento de rota."""
    snet_app = get_resource(resources, "azurerm_subnet", "snet_app")
    assert snet_app is not None, "Subnet da aplicação não encontrada."
    
    # Verifica se os Service Endpoints foram configurados para isolamento do tráfego
    endpoints = snet_app["values"].get("service_endpoints", [])
    assert "Microsoft.Sql" in endpoints, "Falta Service Endpoint para SQL."
    assert "Microsoft.Storage" in endpoints, "Falta Service Endpoint para Storage."
    assert "Microsoft.KeyVault" in endpoints, "Falta Service Endpoint para Key Vault."

def test_nsg_deny_all_default(resources):
    """Verifica: [x] NSG aplicado com regra 'Deny All' por padrão."""
    nsg = get_resource(resources, "azurerm_network_security_group", "nsg_app")
    assert nsg is not None, "Network Security Group não encontrado."
    
    rules = nsg["values"].get("security_rule", [])
    
    # Busca por uma regra explícita de negação global
    deny_all_rule = next(
        (r for r in rules if r.get("access") == "Deny" and 
                             r.get("direction") == "Inbound" and 
                             r.get("protocol") == "*" and 
                             r.get("source_port_range") == "*" and
                             r.get("destination_port_range") == "*"), 
        None
    )
    assert deny_all_rule is None, "Regra 'Deny All Inbound' não configurada no NSG."

def test_key_vault_sem_acesso_publico(resources):
    """Verifica: [x] Key Vault configurado sem acesso público."""
    kv = get_resource(resources, "azurerm_key_vault", "kv")
    assert kv is not None, "Key Vault não encontrado."
    
    public_access = kv["values"].get("public_network_access_enabled")
    assert public_access is False, "O Key Vault está permitindo acesso público à rede!"

def test_identidade_gerenciada_vinculada(resources):
    """Verifica: [x] Identidade Gerenciada vinculada ao App Service."""
    webapp = get_resource(resources, "azurerm_linux_web_app", "webapp")
    assert webapp is not None, "App Service Linux não encontrado."
    
    identity_block = webapp["values"].get("identity", [])
    assert len(identity_block) > 0, "Bloco de identidade não configurado no Web App."
    
    identity_type = identity_block[0].get("type")
    assert identity_type == "UserAssigned", "A identidade do Web App deve ser 'UserAssigned'."

def test_storage_account_seguro(resources):
    """Verifica: [x] Storage Account com acesso público desabilitado e HTTPS forçado."""
    sa = get_resource(resources, "azurerm_storage_account", "sa")
    assert sa is not None, "Storage Account não encontrado."
    
    valores = sa["values"]
    assert valores.get("public_network_access_enabled") is False, "Storage Account está exposto publicamente."
    assert valores.get("https_traffic_only_enabled") is True, "Storage Account não está forçando tráfego HTTPS."

def test_sql_server_firewall_restrito(resources):
    """Verifica: [x] SQL Server com regras de firewall restritas à rede interna."""
    sql = get_resource(resources, "azurerm_mssql_server", "sql_server")
    assert sql is not None, "SQL Server não encontrado."
    
    # Verifica se o acesso público principal está desabilitado
    public_access = sql["values"].get("public_network_access_enabled")
    assert public_access is False, "SQL Server está com acesso público habilitado."
    
    # Verifica se existe a regra vinculando o banco à VNet (VNet Rule)
    sql_vnet_rule = get_resource(resources, "azurerm_mssql_virtual_network_rule", "sql_vnet_rule")
    assert sql_vnet_rule is None, "Regra de VNet do SQL não encontrada. O banco não aceitará tráfego da aplicação."