# Análise de QA dos Testes vs Especificação

## DESCOBERTA DO ESCOPO DA ANÁLISE (OBRIGATÓRIA)

### 1) Arquivos descobertos e utilizados
- **Arquivos de teste:**
  - `tests/unit_tests.py`
  - `tests/integration_tests.py`
- **Arquivo de implementação relevante aos requisitos:**
  - `main-v3.tf`
- **Arquivo de instruções/rubrica de avaliação:**
  - `review.md`

### 2) Fonte de requisitos autorizada escolhida
- Como não foi fornecido um arquivo de especificação funcional separado no escopo permitido, a fonte de requisitos utilizada foi o **checklist funcional explicitado pelos próprios testes unitários**:
  - `tests/unit_tests.py:38`
  - `tests/unit_tests.py:49`
  - `tests/unit_tests.py:67`
  - `tests/unit_tests.py:75`
  - `tests/unit_tests.py:86`
  - `tests/unit_tests.py:95`

### 3) Arquivos esperados ausentes
- **Ausente no escopo permitido:** arquivo dedicado de prompt/especificação funcional (por exemplo `prompt.md`, `task.md`, `README` com requisitos formais).
- A análise foi continuada com as evidências disponíveis nos arquivos permitidos.

---

## BLOCO 1 — COBERTURA DE REQUISITOS

### Mapeamento requisito atômico → testes

| Requisito atômico | Status | Evidências |
|---|---|---|
| VNet e Subnets criadas com isolamento de rota | **coberto** | Unitário valida subnet e service endpoints (`tests/unit_tests.py:37-46`); integração valida VNet e subnets (`tests/integration_tests.py:81-99`); Terraform define VNet/subnets/endpoints (`main-v3.tf:45-65`, `main-v3.tf:57`) |
| NSG aplicado com regra “Deny All” por padrão | **parcial** | Existe teste dedicado (`tests/unit_tests.py:48-65`), porém a asserção verifica ausência da regra (`is None`); integração valida apenas regra AllowHTTPS (`tests/integration_tests.py:100-111`); Terraform mostra regra AllowHTTPS (`main-v3.tf:72-82`) |
| Key Vault sem acesso público | **coberto** | Unitário valida `public_network_access_enabled` false (`tests/unit_tests.py:66-72`); Terraform define false (`main-v3.tf:100`) |
| Identidade gerenciada vinculada ao App Service | **coberto** | Unitário valida identidade UserAssigned (`tests/unit_tests.py:74-83`); Terraform define identity block (`main-v3.tf:172-175`) |
| Storage Account com acesso público desabilitado e HTTPS forçado | **coberto** | Unitário valida ambos atributos (`tests/unit_tests.py:85-92`); Terraform define ambos (`main-v3.tf:128-129`) |
| SQL Server com firewall restrito à rede interna | **parcial** | Unitário valida `public_network_access_enabled` false e checa regra de VNet (`tests/unit_tests.py:94-105`), mas a asserção da VNet rule verifica ausência (`is None`); Terraform define `public_network_access_enabled = true` (`main-v3.tf:144`) |

### Análise de lacunas (somente requisitos **ausentes**)

Nenhum requisito do conjunto selecionado está totalmente ausente de testes.

**Pontuação do Bloco 1: 8/10**

**Conclusões**
- Problema: A cobertura do requisito de “Deny All” no NSG é parcial, pois a validação não assegura de forma forte a presença da regra esperada.
- Problema: A cobertura do requisito de firewall restrito no SQL é parcial, com verificação fraca da regra de VNet e evidência conflitante na infraestrutura declarada.

**Resumo**
Os requisitos do checklist estão majoritariamente cobertos, mas dois controles de segurança críticos (NSG default deny e isolamento de firewall do SQL) permanecem com garantia fraca no conjunto atual de testes.

---

## BLOCO 2 — FORA DO ESCOPO

Testes sem requisito correspondente explícito no checklist selecionado:

1. `test_resource_group_exists` (`tests/integration_tests.py:74-79`)
   - Lógica fantasma: valida localização fixa (`eastus`) e estado de provisionamento.
   - Motivo fora do escopo: o checklist não define requisito de região nem de `provisioning_state`.

2. `test_webapp_exists_and_is_running` (parte de estado) (`tests/integration_tests.py:121-123`)
   - Lógica fantasma: valida `state == "Running"`.
   - Motivo fora do escopo: o checklist trata de identidade e HTTPS, não de estado operacional em execução.

3. `test_storage_account_connectivity` (`tests/integration_tests.py:125-139`)
   - Lógica fantasma: valida conectividade data plane (listagem de containers) via SDK Blob.
   - Motivo fora do escopo: o checklist de storage aborda postura de segurança (acesso público/HTTPS), não teste de conectividade operacional.

**Pontuação do Bloco 2: 7/10**

**Resultados**
- Problema: Há validações de região e estado de provisionamento sem requisito correspondente no checklist.
- Problema: Há validação de estado de execução do Web App sem requisito correspondente no checklist.
- Problema: Há validação de conectividade de data plane sem requisito correspondente no checklist.

**Resumo**
Embora boa parte da suíte esteja alinhada ao checklist, há expansão de escopo para verificações operacionais que não foram explicitamente solicitadas.

---

## BLOCO 3 — QUALIDADE DOS TESTES UNITÁRIOS

### Testes unitários são genuínos?
**Sim, são genuínos.** Eles validam estrutura/atributos de `plan.json` sem chamadas de rede reais e sem dependência de infraestrutura ativa (`tests/unit_tests.py:8-105`).

### Análise de lacunas no nível unitário
- Cobertura **parcial** para “NSG com Deny All por padrão” (`tests/unit_tests.py:48-65`).
- Cobertura **parcial** para “SQL restrito à rede interna” (`tests/unit_tests.py:94-105`).

### Problemas detectados
- Problema: Em `test_nsg_deny_all_default`, a asserção usa `deny_all_rule is None`, o que não assegura fortemente o requisito descrito no próprio teste (`tests/unit_tests.py:56-65`).
- Problema: Em `test_sql_server_firewall_restrito`, a asserção da VNet rule usa `sql_vnet_rule is None`, tornando a validação do requisito fraca (`tests/unit_tests.py:103-105`).
- Problema: Predomínio de caminhos positivos; baixa profundidade de cenários negativos.

### Avaliação de caminhos negativos (explícita)
- Entradas/parâmetros inválidos ou ausentes: **não testado**.
- Falhas de permissão/autorização: **não testado**.
- Recurso não encontrado/dependência indisponível: **parcialmente testado** (`FileNotFoundError` e `KeyError` nas fixtures, `tests/unit_tests.py:11-23`).
- Condições de contorno (coleções vazias, zero, máximos): **não testado**.
- Propagação de erros (exceções lançadas/tratadas): **parcialmente testado** via `pytest.fail` nas fixtures (`tests/unit_tests.py:14-15`, `tests/unit_tests.py:22-23`).

**Pontuação do Bloco 3: 4/10**
