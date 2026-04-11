# Mapa de Leitura

## Princípio

Esta KB foi organizada para seguir o fluxo natural de compreensão do produto:

1. entender o que o `Logic Arena` está tentando ser;
2. entender como o sistema está montado hoje;
3. entender onde estão as tensões arquiteturais e de produto;
4. entender o plano concreto das próximas implementações.

## Ordem recomendada

### Bloco 1 — Produto

- [[../01_Produto/Visão Geral do Produto]]

Comece aqui para alinhar o problema que o sistema resolve, o público atual, o recorte do MVP e a direção do produto.

### Bloco 2 — Arquitetura

- [[../03_Arquitetura/Visão Arquitetural]]
- [[../03_Arquitetura/Decisões Arquiteturais]]

Esse bloco mostra o desenho atual do sistema, suas fronteiras e as decisões que explicam por que ele foi montado assim.

### Bloco 3 — Bounded contexts

- [[../02_Bounded_Contexts/Autenticação e Sessão]]
- [[../02_Bounded_Contexts/Catálogo de Exercícios]]
- [[../02_Bounded_Contexts/Submissão, Runner e Correção]]
- [[../02_Bounded_Contexts/Revisão com IA]]
- [[../02_Bounded_Contexts/Arena Frontend e Experiência]]
- [[../02_Bounded_Contexts/Progressão, History e Gamificação]]
- [[../02_Bounded_Contexts/Operações, Deploy e CI-CD]]

Essas notas são o coração da KB. Cada uma tenta explicar o módulo como código, fluxo e decisão de produto ao mesmo tempo.

### Bloco 4 — Roadmap

- [[../04_Milestones/Mapa de Milestones]]
- [[../04_Milestones/M1 - Integridade da Progressão]]
- [[../04_Milestones/M2 - Taxonomia e Navegação Canônica]]
- [[../04_Milestones/M3 - Ranking e Gamificação Útil]]
- [[../04_Milestones/M4 - Catálogo Avançado e Projetos Integradores]]

Essas notas conectam o estado atual com o que ainda precisa ser construído.

### Bloco 5 — Execução com agentes

- [[../05_Agentes/Playbook de Implementação com Subagentes]]

Esse bloco traduz milestones em rodadas de implementação passíveis de delegação.

## Como usar no Obsidian

- abra esta pasta do projeto como vault secundário, ou apenas a pasta `kb/`;
- use a nota [[Logic Arena KB]] como MOC principal;
- use o canvas do mapa para leitura visual e sequencial.
