# Contribuindo com o Logic Arena

## Objetivo deste guia

Este projeto ainda está em fase de evolução rápida. Por isso, contribuir bem aqui não significa só alterar código: significa também preservar a clareza do produto, da arquitetura e da documentação.

## Antes de abrir qualquer mudança

1. Leia o [`README.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/README.md).
2. Passe pelo índice da KB em [`kb/00_MOC/Logic Arena KB.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/00_MOC/Logic%20Arena%20KB.md).
3. Identifique qual bounded context você está alterando.
4. Veja se já existe uma milestone ou decisão arquitetural cobrindo aquele ponto.

## O que esperamos de uma boa contribuição

- mudança pequena, clara e rastreável;
- escopo explícito;
- código consistente com a direção atual do produto;
- documentação atualizada no mesmo ciclo da implementação;
- preocupação com a experiência do estudante, não só com a engenharia.

## Fluxo recomendado

1. Escolha uma tarefa dentro de um bounded context claro.
2. Leia a nota correspondente da KB.
3. Faça a mudança técnica.
4. Atualize a documentação afetada.
5. Verifique os fluxos principais localmente.

## Quando atualizar a KB

Atualize a KB sempre que a mudança:

- alterar arquitetura;
- criar ou remover um fluxo;
- mudar a navegação ou a experiência do produto;
- introduzir um novo contrato de API;
- mudar regras de progressão, ranking ou catálogo;
- afetar deploy, operação ou CI/CD.

## Convenções práticas

- documentação em `pt-BR`, salvo termos técnicos em inglês quando isso for mais preciso;
- evitar notas soltas sem contexto;
- preferir explicar `por que` uma escolha foi feita, não só `o que` foi mudado;
- se houver tradeoff, registrar o tradeoff;
- se a mudança tocar mais de um bounded context, deixar isso explícito.

## Estrutura relevante

- `backend/`: API, modelos, serviços e migrations
- `frontend/`: landing, tutorial, arena autenticada e estado do usuário
- `runner_service/`: execução isolada de código
- `kb/`: base de conhecimento do projeto

## Verificações mínimas

### Backend

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
.venv/bin/python manage.py check
```

### Frontend

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/frontend"
npm run build
```

### Infra local

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app"
docker compose up -d postgres runner
```

## Contribuições de produto e UX

Se a contribuição for mais de produto/UX do que de código, o esperado é:

- atualizar a milestone correspondente;
- registrar a hipótese de melhoria;
- explicitar o impacto esperado no comportamento do usuário;
- manter continuidade com o design token e com a identidade atual do Logic Arena.

## Contribuições orientadas por IA e subagentes

O projeto foi estruturado para suportar trabalho incremental com agentes. Antes de delegar uma tarefa:

- defina o bounded context responsável;
- deixe o objetivo e os limites da mudança claros;
- atualize a nota da milestone para refletir o escopo da rodada.

O playbook específico para isso está em [`kb/05_Agentes/Playbook de Implementação com Subagentes.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/05_Agentes/Playbook%20de%20Implementa%C3%A7%C3%A3o%20com%20Subagentes.md).
