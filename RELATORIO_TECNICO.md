# Relatório Técnico — Wallet API

**Aluno:** Lucas Miguel — RA 2410578 — Engenharia de Software, UniEVANGÉLICA
**Data:** 17/11/2026
**Repositório:** https://github.com/lucasmiguel2005/projeto-self-testing-ci

## 1. Visão geral

A Wallet API é uma API REST simplificada de conciliação bancária e carteira digital, desenvolvida em Python com FastAPI, SQLAlchemy e SQLite em memória. O foco do trabalho é a qualidade: uma suíte de self-testing em três níveis (unitário, integração e E2E), desenvolvimento orientado a testes (TDD), uma estratégia de branching documentada e um pipeline de integração contínua no GitHub Actions com verificação mínima de cobertura.

## 2. Especificação de requisitos (SRS)

### 2.1 Requisitos funcionais

| ID | Requisito |
|----|-----------|
| RF01 | Criar contas digitais com saldo inicial. |
| RF02 | Consultar uma conta e o seu saldo. |
| RF03 | Transferir saldo entre contas, rejeitando saldo insuficiente, valor zero ou negativo e transferência de uma conta para ela mesma. |
| RF04 | Garantir idempotência da transferência por meio da chave `Idempotency-Key`: repetir a mesma chave não transfere novamente nem notifica novamente o anti-fraude. |
| RF05 | Consultar o extrato de uma conta com filtros por data e por tipo de transação (débito ou crédito). |
| RF06 | Notificar o gateway anti-fraude (fictício) a cada transferência concluída e bloquear transferências que envolvam conta com cadastro irregular. |

### 2.2 Requisitos não funcionais

| ID | Requisito |
|----|-----------|
| RNF01 | Valores monetários tratados com `Decimal` na aplicação e armazenados em centavos inteiros no banco, evitando erros de arredondamento. |
| RNF02 | Cobertura mínima de 85% de linhas e 80% de branches, verificada automaticamente no pipeline (coverage gate). |
| RNF03 | Atomicidade: a atualização dos dois saldos e o registro das duas transações ocorrem na mesma transação de banco de dados. |
| RNF04 | Organização em camadas: domain, services, repositories e controllers. |
| RNF05 | Pipeline de CI disparado automaticamente em eventos de push e pull request. |
| RNF06 | Erros de negócio devolvidos com códigos HTTP coerentes: 404, 422 e 403. |

### 2.3 Interface da API

| Método e rota | Descrição | Respostas |
|---------------|-----------|-----------|
| `POST /contas` | Cria uma conta (`titular`, `saldo_inicial`). | 201 |
| `GET /contas/{numero}` | Consulta uma conta. | 200, 404 |
| `POST /transferencias` | Transfere valor entre contas. Exige o cabeçalho `Idempotency-Key`. | 200, 403, 404, 422 |
| `GET /contas/{numero}/extrato` | Extrato com filtros opcionais `data_inicio`, `data_fim` e `tipo`. | 200, 404 |

## 3. Arquitetura

- **domain:** regras de negócio puras, sem dependências externas (`Conta` e a função `transferir`).
- **services:** `TransferenciaService`, que orquestra a transferência (idempotência, validação cadastral, persistência e notificação ao anti-fraude); `AntiFraudeClient`, que envia o aviso ao gateway por HTTP; e `ValidadorCadastral`, que representa a consulta ao cadastro externo.
- **repositories:** `ContaRepository`, com SQLAlchemy sobre SQLite. Os modelos `ContaModel` e `TransacaoModel` guardam os valores em centavos.
- **controllers:** aplicação FastAPI em `src/controllers/api.py`, que traduz exceções de negócio em respostas HTTP.

A criação das dependências é feita por uma função `criar_app`, o que permite injetar um repositório em memória e um Mock do anti-fraude nos testes.

## 4. Estratégia de branching e controle de versão

Foi adotado o **Trunk-Based Development**: a `main` é o tronco e cada funcionalidade foi desenvolvida em uma branch curta, integrada à `main` por pull request no GitHub. O único commit feito diretamente na `main` foi o commit inicial de estrutura do projeto (`chore`). Os commits seguem convenção semântica (`test:`, `feat:`, `refactor:`, `chore:`, `ci:`).

| Branch | Entrega |
|--------|---------|
| `feat/conta-e-saldo` | Entidade `Conta`: criar, debitar, creditar e validar valores (TDD). |
| `feat/transferencia` | Transferência entre contas e idempotência no `TransferenciaService` (TDD). |
| `feat/integracao-banco-antifraude` | Repositório SQLite em memória, Mock do anti-fraude, Stub cadastral e extrato. |
| `feat/api-e2e` | API FastAPI e testes E2E. |
| `feat/ci-pipeline` | Pipeline do GitHub Actions, coverage gate e este relatório. |

## 5. Estratégia de testes

A suíte tem **27 testes** organizados na pirâmide de testes:

| Nível | Pasta | Testes | O que valida |
|-------|-------|--------|--------------|
| Unitário | `tests/unit` | 13 | Regras de `Conta`, da função `transferir` e do serviço, com um repositório falso. |
| Integração | `tests/integration` | 8 | Serviço e repositório com SQLite em memória, Mock e Stub. |
| E2E | `tests/e2e` | 6 | Fluxo completo por requisições HTTP com o `TestClient` do FastAPI. |

### 5.1 TDD (Red-Green-Refactor)

O desenvolvimento da entidade `Conta` seguiu o ciclo com commits separados para cada fase. Trecho do `git log --oneline`, do mais recente para o mais antigo:

```
01c4b62 refactor: extrai validação de valor para um método
650e913 feat: creditar aumenta o saldo (green)
8a7350a test: creditar aumenta o saldo e valida o valor (red)
42ea8bf feat: valida valor positivo no débito (green)
2d99a97 test: rejeita valor zero ou negativo no débito (red)
8e44073 feat: bloqueia débito com saldo insuficiente (green)
a20f8a3 test: não permite debitar mais que o saldo (red)
9f3b995 feat: debitar reduz o saldo (green)
94d7e8c test: debitar reduz o saldo (red)
b0dc1df feat: criar conta com saldo inicial (green)
d92f6b5 test: conta nova começa com o saldo inicial (red)
b948ccc chore: estrutura inicial do projeto
```

A transferência e a idempotência, o repositório com anti-fraude e a API também foram feitas com o teste escrito antes do código (commits `test: ... (red)` seguidos de `feat: ... (green)`).

### 5.2 Test doubles: Mock e Stub

- **Mock (verificação de saída):** `Mock(spec=AntiFraudeClient)` verifica as interações com o serviço externo: `assert_called_once_with` confere a contagem e os parâmetros enviados (chave, origem, destino e valor), `call_count == 1` confirma que uma chave repetida não notifica de novo e `assert_not_called` confirma que transferências recusadas não notificam.
- **Stub (entrada controlada):** `ValidadorCadastralStub` devolve respostas fixas de validação cadastral e permite simular uma conta com cadastro irregular, sem lógica própria, para provar que a transferência é bloqueada.
- **Fake:** nos testes unitários, um `RepositorioFalso` em memória isola a lógica do serviço do banco.

### 5.3 Banco em memória

Os testes de integração e E2E usam SQLite em memória (`sqlite://`), criado do zero para cada teste, o que garante isolamento entre eles.

## 6. Cobertura de código

Medida com `pytest-cov` (com `--cov-branch`) e verificada pelo script `scripts/verificar_cobertura.py`:

| Métrica | Resultado | Meta |
|---------|-----------|------|
| Linhas | **95.2%** | 85% |
| Branches | **86.1%** | 80% |

As duas metas foram atingidas. O ponto de menor cobertura é `AntiFraudeClient` (cerca de 40%), porque nos testes o gateway é substituído por um Mock e a chamada HTTP real não é exercitada.

## 7. Pipeline de integração contínua

O arquivo `.github/workflows/ci.yml` é disparado em eventos de `push` (branches `main`, `feat/**` e `hotfix/**`) e de `pull_request` para a `main`. Etapas:

1. Baixar o código e instalar o Python 3.13 e as dependências.
2. Linter e análise estática com **ruff**.
3. Execução separada dos testes unitários, de integração e E2E.
4. Execução da suíte completa com cobertura de linhas e de branches.
5. **Coverage gate:** `scripts/verificar_cobertura.py` falha o pipeline se a cobertura ficar abaixo de 85% (linhas) ou 80% (branches).
6. Publicação como artefato do build do `coverage.xml`, do relatório HTML de cobertura e do resultado dos testes (logs).

## 8. Desempenho, limitações e próximos passos

Esta entrega tem limitações que são registradas aqui de forma transparente:

- **Teste de carga:** o script com Locust (50 requisições simultâneas no endpoint de transferência, registrando taxa de erro e latência média) **não foi executado nesta entrega**, portanto não há métricas de desempenho.
- **Concorrência:** a idempotência é mantida na memória do processo e ainda não existe uma trava (lock) protegendo transferências simultâneas sobre a mesma conta. Em produção, a chave de idempotência deve ser persistida no banco e a transferência deve usar controle de concorrência (lock ou transação com isolamento adequado).
- **Precisão decimal:** valores com mais de duas casas decimais ainda não são rejeitados explicitamente, e o armazenamento em centavos trunca o excedente.
- **Proteção da `main`:** a regra de branch protection que exige o pull request e o sucesso do check de testes antes do merge ainda deve ser ativada nas configurações do repositório.
- **Correções emergenciais:** não houve branches `hotfix/` nesta entrega; a integração ocorreu por merges de pull request documentados na seção 4.
- **Anti-fraude real:** a chamada HTTP do `AntiFraudeClient` não é exercitada pelos testes automatizados.

## 9. Como executar

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
ruff check .
python scripts/verificar_cobertura.py
uvicorn src.main:app --reload
```

A variável opcional `ANTIFRAUDE_URL` (ver `.env.example`) define o endereço do gateway anti-fraude. Sem ela, a notificação é ignorada.