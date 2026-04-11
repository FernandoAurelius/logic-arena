# Visão Arquitetural

## Leitura rápida

O sistema atual é pequeno, mas já tem separação funcional suficiente para evoluir sem colapsar tudo num único processo:

- `frontend/`: superfície pública e arena autenticada;
- `backend/`: API principal, persistência e orquestração;
- `runner_service/`: execução isolada de código;
- `PostgreSQL`: persistência de usuários, exercícios, casos de teste e submissões;
- `Gemini via Agno`: geração de feedback e conversa contextual.

## Fluxo ponta a ponta

```mermaid
flowchart LR
    A["Landing / Login"] --> B["Frontend Vue"]
    B --> C["API Django Ninja"]
    C --> D["PostgreSQL"]
    C --> E["Runner Service"]
    C --> F["Agno + Gemini"]
    E --> C
    F --> C
    C --> B
```

## Fronteiras principais

### 1. Frontend

Responsável por:

- controlar sessão;
- carregar catálogo e detalhes dos exercícios;
- capturar o código digitado;
- submeter solução;
- exibir console, feedback, chat e histórico;
- manter parte da gamificação local.

### 2. Backend principal

Responsável por:

- autenticar o usuário;
- persistir o estado durável do sistema;
- modelar exercícios e submissões;
- chamar o runner;
- normalizar correção;
- disparar e persistir revisão com IA.

### 3. Runner

Responsável por:

- executar código Python isoladamente;
- devolver `stdout`, `stderr` e status de execução;
- não carregar responsabilidade de domínio pedagógico.

### 4. IA

Responsável por:

- traduzir resultados de teste em feedback;
- explicar acertos e erros;
- continuar uma conversa contextual sobre uma submissão específica.

## Por que a arquitetura atual faz sentido

Mesmo sendo um MVP, separar backend principal e runner já traz três vantagens:

- impede que a execução arbitrária fique dentro do processo principal da API;
- deixa a avaliação mais observável;
- prepara o terreno para limites de execução, hardening e futuras linguagens.

## O que ainda não está maduro

- o modelo de domínio de `Exercise` ainda é raso e não suporta categorias/trilhas;
- a progressão de XP vive no frontend e ainda não tem guardrails;
- o ranking ainda não existe;
- parte da lógica de produto ainda está implícita em UI, não em domínio persistido.

## Leituras seguintes

- [[Decisões Arquiteturais]]
- [[../02_Bounded_Contexts/Submissão, Runner e Correção]]
- [[../02_Bounded_Contexts/Revisão com IA]]
