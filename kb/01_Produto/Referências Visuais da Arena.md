# Referências Visuais da Arena

## Status
Em `2026-04-15`, as referências visuais geradas no Stitch foram materializadas dentro do repo e passam a ser a base visual oficial para a continuação das fases de frontend da Arena.

## Local canônico no repo
- [frontend/docs/stitch-references/2026-04-15-learning-platform-home/README.md](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/frontend/docs/stitch-references/2026-04-15-learning-platform-home/README.md)

## Decisão
- a shell única da Arena continua sendo o princípio estrutural
- as referências do Stitch passam a orientar a execução visual das superfícies faltantes
- o design system de base para a Arena passa a seguir a direção descrita em `neo_syntax_console/DESIGN.md`

## Mapeamento de uso
- `objective_item`
  - referências: `arena_item_objetivo_com_est_mulo_1`, `arena_item_objetivo_com_est_mulo_2`, `arena_diagn_stico_de_comportamento_exam_like`
- `restricted_code`
  - referências: `arena_manipula_o_restrita_corrija_o_snippet`, `arena_modo_preenchimento_idle`, `arena_modo_preenchimento_resultado`
- `code_lab`
  - referências: `arena_lab_multi_arquivo_v1`, `arena_lab_multi_arquivo_sucesso`, `arena_resultado_e_an_lise_de_ia`
- `contract_behavior_lab`
  - referências: `arena_api_lab_contract_validation`, `arena_lab_de_componentes_ui`, `arena_falha_de_reatividade_ui`
- `assessment_container`
  - referências: `logic_arena_assessment_em_progresso`, `logic_arena_resultado_do_assessment`

## Implicação para o planejamento
- Fase 1 FE: finalização visual e consolidação da shell com esse baseline
- Fase 2 FE: `objective_item` deve nascer já alinhado a essas referências
- próximas famílias do plano não devem mais sair de prompt isolado; devem partir destas bases já versionadas
