# Definindo o conteúdo do documento Markdown com base nos requisitos solicitados
markdown_content = """# Documento de Requisitos: Provisionamento de Infraestrutura Segura (Azure via LocalStack)

## 1. Visão Geral do Projeto
O objetivo deste projeto é estabelecer um ambiente em nuvem de alta disponibilidade, escalável e rigorosamente seguro. A arquitetura foi desenhada para garantir o isolamento de dados sensíveis, a rastreabilidade das operações e a total conformidade com as políticas de governança e segurança da informação da organização, alinhando-se aos pilares do *Azure Well-Architected Framework*.

---

## 2. Arquitetura de Referência
A arquitetura baseia-se no modelo de camadas (N-Tier) para garantir o isolamento de funções e a proteção de dados sensíveis.

### 2.1. Topologia de Rede (Microsoft.Network)
* **Virtual Network (VNet):** Uma rede lógica isolada com endereçamento CIDR privado.
* **Subnets Segregadas:**
    * **Sub-rede de Aplicação:** Destinada exclusivamente aos serviços de computação (App Services).
    * **Sub-rede de Dados:** Destinada aos serviços de persistência (SQL e Storage), sem rota direta para a internet.
* **Conectividade Privada:** Utilização de Service Endpoints para garantir que o tráfego entre a aplicação e o banco de dados nunca saia da rede privada.

### 2.2. Camada de Computação (Microsoft.Web)
* **App Service Plan:** Configuração de plano de serviço Linux para hospedagem de containers ou código.
* **Web App:** Instância isolada configurada para aceitar apenas tráfego criptografado (HTTPS).

---

## 3. Requisitos de Segurança
A segurança é implementada através do princípio de "Defesa em Profundidade".

### 3.1. Gestão de Identidade e Acesso (IAM)
* **Managed Identities:** Uso obrigatório de Identidades Gerenciadas Atribuídas pelo Usuário. Nenhum serviço deve utilizar chaves de acesso estáticas ou strings de conexão "hardcoded".
* **RBAC (Role-Based Access Control):** Atribuição de permissões baseada no princípio do menor privilégio para a identidade da aplicação acessar o Key Vault e o Storage.

### 3.2. Proteção de Segredos (Microsoft.KeyVault)
* **Cofre de Chaves:** Centralização de todos os certificados, chaves criptográficas e segredos.
* **Políticas de Acesso:** O acesso ao cofre deve ser restrito ao administrador do sistema e à identidade gerenciada da aplicação (apenas leitura).
* **Soft-Delete:** Habilitação de proteção contra exclusão acidental.

### 3.3. Segurança de Perímetro (Network Security Groups)
* **Firewall de Rede (NSG):** * **Inbound:** Permitir apenas tráfego HTTPS (porta 443) vindo de fontes confiáveis.
    * **Outbound:** Restringir a saída apenas para os endpoints necessários do Azure e serviços de atualização.

---

## 4. Requisitos de Armazenamento e Discos
O armazenamento deve garantir a integridade e a confidencialidade dos dados em repouso.

### 4.1. Discos Gerenciados (Managed Disks)
* **Criptografia:** Todos os discos associados a serviços de computação devem utilizar criptografia em repouso (SSE) gerenciada pela plataforma.
* **Redundância:** Configuração de Redundância Local (LRS) para simulação de resiliência.

### 4.2. Armazenamento de Objetos (Microsoft.Storage - Blobs)
* **Acesso Privado:** O acesso público anônimo deve ser explicitamente desabilitado no nível da conta de armazenamento.
* **Transferência Segura:** Exigência de protocolo SMB 3.0 ou HTTPS para todas as operações.
* **Imagens e Ativos:** Armazenamento em containers específicos com políticas de imutabilidade, se necessário, para prevenir alterações não autorizadas.

---

## 5. Requisitos de Banco de Dados (Microsoft.Sql)
* **Firewall do SQL:** Bloqueio de acesso a todos os IPs, permitindo apenas o tráfego originado da VNet da aplicação.
* **Criptografia de Dados Transparente (TDE):** Ativação obrigatória para proteger os arquivos de dados e logs contra acesso físico não autorizado.
* **Auditoria:** Configuração de logs de auditoria direcionados para uma conta de armazenamento de logs para monitoramento de atividades suspeitas.

---

## 6. Checklist de Conformidade para Implementação
- [ ] VNet e Subnets criadas com isolamento de rota.
- [ ] NSG aplicado com regra "Deny All" por padrão.
- [ ] Key Vault configurado sem acesso público.
- [ ] Identidade Gerenciada vinculada ao App Service.
- [ ] Storage Account com acesso público desabilitado e HTTPS forçado.
- [ ] SQL Server com regras de firewall restritas à rede interna.