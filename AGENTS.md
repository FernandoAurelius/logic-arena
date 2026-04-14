# AGENTS

## Escopo

Este repositório contém o produto `Logic Arena`, incluindo `backend`, `frontend`, `runner_service` e a KB do projeto.

## Regras de trabalho

- a documentação do projeto deve ser escrita em `pt-BR` por padrão
- mudanças relevantes de arquitetura, produto, operação ou fluxo devem atualizar a KB no mesmo ciclo
- bounded contexts do backend vivem em `backend/apps/*`
- a estrutura canônica do frontend segue `Feature-Sliced Design` com `shared`, `entities`, `features`, `widgets` e `pages`
- `backend/apps/arena` existe como shell de integração e compatibilidade, não como destino para regra nova de negócio

## Boy Scout Rule

Sempre que possível, aplique a `Boy Scout Rule`: deixe o código um pouco melhor do que estava quando você entrou.

Na prática, isso significa:

- reduzir duplicação desnecessária (`DRY`) quando a extração for clara e local
- melhorar separação de responsabilidades (`SOLID`) quando houver ganho real de leitura, ownership ou testabilidade
- empurrar código para a camada correta do sistema quando houver desalinhamento evidente de arquitetura
- preferir pequenos refactors oportunistas e seguros em vez de conviver com degradação óbvia

## Limites da regra

Essa regra não autoriza:

- rewrites oportunistas fora do escopo
- grandes refactors sem validação
- mover estrutura por purismo quando não houver ganho concreto

O objetivo é manter a evolução do produto fluida sem deixar dívida fácil se acumular por inércia.
