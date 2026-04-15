# Referências Visuais Stitch

Base visual oficial trazida em `2026-04-15` para finalizar a Fase 1 do frontend e orientar todas as próximas fases da Arena.

## Origem
- arquivo-fonte importado: `stitch_ai_learning_platform_home(6).zip`
- data de materialização no repo: `2026-04-15`
- diretório canônico no repo: `frontend/docs/stitch-references/2026-04-15-learning-platform-home`

## Como usar
- usar estas telas como **baseline visual** para layout, densidade, hierarquia, tratamento de estados e linguagem de superfície da Arena
- preservar a ideia de **shell única** com superfícies especializadas por `surface_key`
- usar o `code.html` como referência estrutural e o `screen.png` como referência visual
- quando houver conflito entre estas referências e o domínio/capacidades atuais, priorizar o domínio canônico e adaptar a UI mantendo a direção visual

## Mapeamento por família e superfície

### `objective_item`
- `objective_choices`
  - `arena_item_objetivo_com_est_mulo_1`
  - `arena_item_objetivo_com_est_mulo_2`
- `objective_classifier`
  - `arena_diagn_stico_de_comportamento_exam_like`

### `restricted_code`
- `restricted_diff`
  - `arena_manipula_o_restrita_corrija_o_snippet`
- `restricted_fill_blanks`
  - `arena_modo_preenchimento_idle`
  - `arena_modo_preenchimento_resultado`

### `code_lab`
- `code_editor_multifile`
  - `arena_lab_multi_arquivo_v1`
  - `arena_lab_multi_arquivo_sucesso`
- feedback/revisão
  - `arena_resultado_e_an_lise_de_ia`

### `contract_behavior_lab`
- `http_contract_lab`
  - `arena_api_lab_contract_validation`
- `component_behavior_lab`
  - `arena_lab_de_componentes_ui`
  - `arena_falha_de_reatividade_ui`

### `assessment_container`
- progresso
  - `logic_arena_assessment_em_progresso`
- resultado agregado
  - `logic_arena_resultado_do_assessment`

## Referência transversal de design system
- `neo_syntax_console/DESIGN.md`

Esse documento é a base de:
- paleta
- tipografia
- tratamento de profundidade
- brutalismo técnico/editorial
- linguagem visual do editor, painéis e CTAs

## Convenções para implementação
- toda tela nova da Arena deve apontar explicitamente para uma referência desta pasta durante a implementação
- toda nova superfície deve declarar qual referência visual está sendo seguida
- se uma mesma família tiver mais de uma referência, usar a de estado `idle` para composição base e a de `resultado/sucesso` para feedback pós-avaliação

## Próximas aplicações
- finalizar a UI de `objective_item` em cima das referências `arena_item_objetivo_com_est_mulo_*` e `arena_diagn_stico_de_comportamento_exam_like`
- evoluir `code_lab` multifile com base em `arena_lab_multi_arquivo_v1` e `arena_lab_multi_arquivo_sucesso`
- usar `arena_resultado_e_an_lise_de_ia` como base do refinamento do painel de revisão canônico
