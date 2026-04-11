# Playbook de Implementação com Subagentes

## Objetivo

Preparar o projeto para rodadas incrementais de implementação com agentes, sem perder contexto nem criar trabalho sobreposto.

## Regra principal

Subagentes devem receber tarefas pequenas, delimitadas e alinhadas a um bounded context claro.

## Fluxo recomendado

1. escolher a milestone ativa;
2. quebrar a milestone em tarefas independentes;
3. atribuir ownership por módulo;
4. garantir que cada subagente escreva apenas em uma fatia previsível do sistema;
5. integrar de volta no fluxo principal;
6. atualizar a KB ao final de cada rodada.

## Exemplo por milestone

### M1 — Integridade da Progressão

- subagente 1: modelagem e migrations do backend
- subagente 2: adaptação de endpoints e schemas
- subagente 3: integração do frontend com novo payload de progresso
- subagente 4: documentação da nova regra de XP

### M2 — Taxonomia e Navegação

- subagente 1: novos modelos de catálogo
- subagente 2: seed e classificação dos exercícios atuais
- subagente 3: redesign de navegação no frontend
- subagente 4: documentação de produto e decisão arquitetural

## O que não delegar mal

- tarefas muito vagas como “melhorar o app”;
- mudanças que escrevem nos mesmos arquivos sem coordenação;
- trabalho bloqueante cujo resultado é necessário imediatamente.

## Entregáveis esperados de cada rodada

- código implementado;
- verificação mínima local;
- atualização da KB;
- registro explícito do que mudou no bounded context.

## Leituras de apoio

- [[../04_Milestones/Mapa de Milestones]]
- [[../03_Arquitetura/Decisões Arquiteturais]]
