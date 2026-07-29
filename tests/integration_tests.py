import os
import pytest
from azure.core.credentials import AccessToken
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.storage.blob import BlobServiceClient

# ==========================================
# CONFIGURAÇÕES DO LOCALSTACK
# ==========================================
# O LocalStack expõe os serviços do Azure na porta 4566
LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "https://localhost.localstack.cloud:4566")
SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000000"

# Variáveis do nosso projeto Terraform
PROJECT_NAME = "secapp"
ENV = "local"
RG_NAME = f"rg-{PROJECT_NAME}-{ENV}"
STORAGE_ACCOUNT_NAME = f"sa{PROJECT_NAME}{ENV}001"

# ==========================================
# MOCK DE AUTENTICAÇÃO
# ==========================================
class LocalStackDummyCredential:
    """
    Simula um token de acesso válido do Azure AD. 
    O LocalStack valida a presença do token, mas ignora a assinatura real localmente.
    """
    def get_token(self, *scopes, **kwargs):
        return AccessToken("localstack-dummy-token", 2000000000)

@pytest.fixture(scope="session")
def credential():
    return LocalStackDummyCredential()

# ==========================================
# FIXTURES DOS CLIENTS (SDKs do Azure)
# ==========================================
@pytest.fixture(scope="session")
def resource_client(credential):
    return ResourceManagementClient(
        credential=credential, 
        subscription_id=SUBSCRIPTION_ID, 
        base_url=LOCALSTACK_ENDPOINT,
        #enforce_https=False
        connection_verify=False
    )

@pytest.fixture(scope="session")
def network_client(credential):
    return NetworkManagementClient(
        credential=credential, 
        subscription_id=SUBSCRIPTION_ID, 
        base_url=LOCALSTACK_ENDPOINT,
        #enforce_https=False
        connection_verify=False
    )

@pytest.fixture(scope="session")
def web_client(credential):
    return WebSiteManagementClient(
        credential=credential, 
        subscription_id=SUBSCRIPTION_ID, 
        base_url=LOCALSTACK_ENDPOINT,
        #enforce_https=False
        connection_verify=False
    )

# ==========================================
# TESTES DE INTEGRAÇÃO
# ==========================================

def test_resource_group_exists(resource_client):
    """Garante que o Resource Group base foi criado com sucesso."""
    rg = resource_client.resource_groups.get(RG_NAME)
    assert rg.name == RG_NAME
    assert rg.location == "eastus"
    assert rg.properties.provisioning_state == "Succeeded"

def test_vnet_and_subnets_exist(network_client):
    """Garante que a VNet e as Subnets segregadas estão de pé."""
    vnet_name = f"vnet-{PROJECT_NAME}-{ENV}"
    vnet = network_client.virtual_networks.get(RG_NAME, vnet_name)
    
    assert vnet.name == vnet_name
    assert vnet.provisioning_state == "Succeeded"
    
    # Valida as subnets
    subnets = {subnet.name: subnet for subnet in vnet.subnets}
    assert "snet-app" in subnets
    assert "snet-database" in subnets
    
    # Valida Service Endpoints na subnet da aplicação
    snet_app = subnets["snet-app"]
    endpoints = [se.service for se in snet_app.service_endpoints]
    assert "Microsoft.Storage" in endpoints
    assert "Microsoft.Sql" in endpoints

def test_nsg_is_applied(network_client):
    """Verifica se o Network Security Group foi criado com as regras de segurança."""
    nsg_name = f"nsg-{PROJECT_NAME}-app"
    nsg = network_client.network_security_groups.get(RG_NAME, nsg_name)
    
    assert nsg.name == nsg_name
    
    # Busca a regra de permissão do HTTPS
    https_rule = next((rule for rule in nsg.security_rules if rule.name == "AllowHTTPS"), None)
    assert https_rule is not None
    assert https_rule.destination_port_range == "443"
    assert https_rule.access == "Allow"

def test_webapp_exists_and_is_running(web_client):
    """Verifica se o App Service foi provisionado e está na plataforma Linux."""
    app_name = f"app-{PROJECT_NAME}-{ENV}"
    
    # Em LocalStack, algumas operações de listagem e get podem ter pequenas variações,
    # mas o get direto pelo nome deve retornar o site.
    webapp = web_client.web_apps.get(RG_NAME, app_name)
    
    assert webapp.name == app_name
    assert webapp.state == "Running"
    assert webapp.https_only is True, "O WebApp deve forçar tráfego HTTPS."

def test_storage_account_connectivity(credential):
    """
    Testa a conectividade da camada de dados usando o SDK de Data Plane (Storage Blob).
    """
    # No LocalStack, as URLs de data plane apontam para a porta 4566
    storage_account_name = "sasecapplocal001" 
    #blob_service_url = f"https://{storage_account_name}.blob.localhost.localstack.cloud:4566"
    blob_service_url = f"https://sasecapplocal001.blob.core.azure.localhost.localstack.cloud:4566"
    #blob_service_url = f"http://127.0.0.1:4566/{storage_account_name}"
    conn_str = ("DefaultEndpointsProtocol=http;"f"AccountName={storage_account_name};""AccountKey=dGVzdGUtbG9jYWxzdGFjaw==;"f"BlobEndpoint={blob_service_url};")
    blob_client = BlobServiceClient.from_connection_string(conn_str, connection_verify=False)
    # Tenta listar os containers para garantir que a conta de armazenamento está viva e respondendo
    containers = list(blob_client.list_containers())
    # Se a chamada não lançar exceção (ex: ResourceNotFoundError), o serviço está no ar.
    assert isinstance(containers, list)