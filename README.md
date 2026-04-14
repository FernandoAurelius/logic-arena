# Logic Arena

`Logic Arena` é uma plataforma de treino prático de lógica de programação orientada a simular avaliação real: o aluno escolhe um exercício, escreve código em um editor de verdade, executa contra testes automatizados, recebe console detalhado, feedback estruturado com IA e pode revisitar sessões anteriores para estudar o próprio raciocínio.

Hoje o projeto está em uma fase de MVP operacional. Ele já resolve o ciclo central de prática, mas está amadurecendo em quatro frentes encadeadas: progressão anti-farm, navegação canônica do banco de exercícios, consolidação de um catálogo real e editável por módulos, e só depois ranking/gamificação útil apoiado nesse catálogo.

## Propósito

O produto existe para atacar um problema muito específico: treinar programação do jeito que ela costuma ser cobrada em contexto de aula e prova prática, sem depender apenas de listas estáticas ou IDEs sem contexto pedagógico.

Em vez de ser só uma coleção de exercícios, o `Logic Arena` quer se tornar uma estação de prática com:

- execução real de código Python em ambiente isolado;
- correção baseada em testes visíveis e ocultos;
- feedback automático com IA após cada submissão;
- histórico restaurável de tentativas, console, revisão e conversa;
- progressão gamificada sem perder valor pedagógico;
- catálogo crescente de exercícios, começando em fundamentos e evoluindo para problemas mais sistêmicos.

## Estado atual do produto

O repositório convive hoje com duas camadas:

- um protótipo inicial na raiz, em `React/Vite`, usado para iterar rápido sobre UX, editor e correção;
- um MVP mais estável em `backend/` + `frontend/` + `runner_service/`, que representa a base arquitetural do produto.

O MVP já possui:

- login mínimo por `nickname + senha`, com criação automática do usuário no primeiro acesso;
- catálogo persistido de exercícios no banco;
- navegação principal por `Módulo -> Trilha -> Exercício`;
- submissões persistidas por usuário e exercício;
- execução assíncrona via runner isolado;
- revisão com IA via `Agno + Gemini`;
- landing pública, arena autenticada e página de ajuda;
- deploy contínuo para produção em [logic-arena.floresdev.com.br](https://logic-arena.floresdev.com.br).

## Estado atual da M4

Hoje a `M2` pode ser lida como **concluída no escopo inicial**, e a `M4` já começou de forma concreta no código.

Isso significa que o projeto já possui, ao mesmo tempo:

- `Navigator` autenticado como superfície real de descoberta;
- `Track Page` como navegação por trilha e progressão;
- contexto de trilha refletido na `Arena`;
- taxonomia mínima funcional com `módulo`, `trilha`, `status`, `exercise_type`, `estimated_time_minutes` e ordem;
- explicações por módulo em superfície dedicada.

E, na frente da `M4`, a base já foi materializada para:

- persistir `LearningModule` como entidade canônica acima de `ExerciseTrack`;
- persistir `ExerciseType` como taxonomia real do formato cognitivo dos exercícios;
- enriquecer trilhas com `goal`, `level_label`, `concept_kicker`, `milestone_*`, conceitos e pré-requisitos;
- enriquecer exercícios com `exercise_type`, `estimated_time_minutes`, `track_position`, `concept_summary` e `pedagogical_brief`;
- expor uma `API interna` de catálogo e manutenção correspondente no `Django admin`;
- popular o primeiro módulo profundo, `Lógica de Programação com Python`, e scaffolds reais para `FastAPI`, `Vue`, `Integração Full-stack` e `OCP 17`.

### Decisão deliberada da M4

`ExerciseCategory` continua existindo no domínio, mas deixa de ser o eixo principal da navegação. Nesta fase, a leitura pública e pedagógica do produto passa a ser:

- `Módulo`
- `Trilha`
- `Exercício`

Categorias permanecem como taxonomia secundária e apoio editorial.

## Para quem o projeto está sendo feito

O recorte atual é deliberadamente pequeno: colegas e estudantes que querem praticar lógica de programação em um formato mais próximo da avaliação prática real. A plataforma ainda não tenta ser uma escola ampla, um judge online genérico ou um LMS completo.

## Autor

Projeto idealizado e mantido por **Miguel Barreto**.

- GitHub: [FernandoAurelius](https://github.com/FernandoAurelius)
- Repositório: [logic-arena](https://github.com/FernandoAurelius/logic-arena)

## Stack

### Backend

- `Python`
- `Django`
- `Django Ninja`
- `PostgreSQL`
- `Agno`
- `Google Gemini`

### Frontend

- `Vue 3`
- `TypeScript`
- `Vite`
- `Monaco Editor`
- `Zodios` gerado a partir de `OpenAPI`
- componentes inspirados em `shadcn-vue`

### Execução de código

- `FastAPI` no `runner_service/`
- execução isolada do código submetido

### Operações

- `Docker Compose` para infraestrutura local mínima
- `Nginx` + `systemd` em produção
- `GitHub Actions` para deploy contínuo

## Mapa do repositório

```text
.
├── backend/                  # API principal, modelos, serviços, migrations e OpenAPI
├── frontend/                 # Aplicação Vue 3 + TS da arena autenticada e da landing
├── runner_service/           # Serviço isolado de execução Python
├── .github/workflows/        # Pipeline de deploy
├── src/                      # Protótipo inicial em React/Vite
├── server.mjs                # API local antiga do protótipo inicial
└── kb/                       # Knowledge base Obsidian-oriented do projeto
```

## Arquitetura em uma leitura rápida

1. O usuário entra pela landing pública.
2. Faz login com `nickname + senha`.
3. O frontend autenticado consome a API principal em `backend/`.
4. Ao submeter código, o backend chama o `runner_service/` para executar a solução.
5. O backend persiste a submissão, calcula status e agenda a revisão com IA.
6. O frontend faz polling da submissão até o feedback ficar pronto.
7. O histórico permite reabrir código, console, revisão automática e conversa com IA.

## Como rodar localmente

### 1. Infra mínima

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app"
docker compose up -d postgres runner
```

Por padrão, o `PostgreSQL` fica em `127.0.0.1:5433`.

### 2. Backend

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
.venv/bin/python -m pip install -e .
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo_exercises
.venv/bin/python manage.py export_openapi
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

O backend exige `GEMINI_API_KEY` em `backend/.env`. Sem essa chave, a aplicação falha na inicialização por design.

### Sincronização editorial do módulo OCP 17

O módulo `Preparatório OCP 17` pode ser reidratrado a partir de um JSON curado de contexto:

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
.venv/bin/python manage.py sync_ocp17_catalog --source "/caminho/para/ocp17_course_context.json" --replace
```

Esse comando:

- atualiza o `LearningModule` `preparatorio-ocp-17`;
- recria as trilhas do módulo com base no JSON;
- persiste conceitos e pré-requisitos por trilha;
- substitui scaffolds antigos por uma estrutura mais fiel ao curso/exame.

### 3. Frontend

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/frontend"
npm install
npm run generate:api
npm run check:architecture
npm run dev
```

Se quiser apontar para outra API:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

### 4. Runner isolado sem Docker

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/runner_service"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8010
```

## Contrato principal da API

Os endpoints centrais do MVP hoje são:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/catalog/navigator`
- `GET /api/catalog/modules/{module_slug}`
- `GET /api/catalog/tracks/{track_slug}`
- `GET /api/catalog/tracks/{track_slug}/explanations/{exercise_slug}`
- `GET /api/exercises/`
- `GET /api/exercises/{slug}`
- `POST /api/exercises/`
- `POST /api/submissions/exercises/{slug}/submit`
- `GET /api/submissions/me`
- `GET /api/submissions/{id}`
- `POST /api/submissions/{id}/review-chat`
- `GET /api/catalog-admin/reference`
- `GET/POST /api/catalog-admin/modules`
- `GET/POST /api/catalog-admin/exercise-types`
- `GET/POST /api/catalog-admin/tracks`
- `PATCH /api/catalog-admin/tracks/{slug}`
- `PATCH /api/catalog-admin/exercises/{slug}/catalog`

## Guardrails arquiteturais

O repositório agora tem checks leves para segurar a arquitetura pós-migração:

- `backend`: `pytest` cobre guardrails de import entre apps e pureza mínima dos módulos `domain/`;
- `frontend`: `npm run check:architecture` falha se reaparecer `src/views`, `src/components`, imports diretos de `@/lib/api/generated` ou violações básicas entre camadas FSD.

Na prática, isso cristaliza o contrato atual:

- `backend/apps/*` é a raiz canônica dos bounded contexts;
- `backend/apps/arena` existe como shell de integração e compatibilidade, não como lugar de regra nova;
- `frontend/src/pages`, `widgets`, `features`, `entities` e `shared` são as camadas oficiais da UI.
- `GET /api/health`

O contrato `OpenAPI` exportado pelo backend vive em [`backend/openapi.json`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend/openapi.json).

## Knowledge Base do projeto

O projeto agora possui uma KB em Markdown orientada a Obsidian dentro de [`kb/`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb).

Ela foi organizada para servir a quatro propósitos:

- onboarding técnico do sistema;
- documentação didática do código existente;
- registro de decisões arquiteturais;
- planejamento incremental das próximas milestones, inclusive para trabalho com subagentes.

O melhor ponto de entrada é:

- [`kb/00_MOC/Logic Arena KB.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/00_MOC/Logic%20Arena%20KB.md)

## Como contribuir

O projeto ainda é pequeno, então o processo de contribuição também é propositalmente simples.

1. Leia este `README`.
2. Leia a KB técnica antes de propor mudanças estruturais.
3. Entenda qual bounded context você está tocando.
4. Registre decisões importantes na KB junto com a mudança.
5. Se a mudança afetar produto, arquitetura ou operação, atualize a documentação correspondente no mesmo PR/commit.

Mais detalhes estão em [`CONTRIBUTING.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/CONTRIBUTING.md).

## Roadmap de curto prazo

As próximas frentes priorizadas hoje são:

- consolidação final da `M4`, removendo a dependência runtime de metadados editoriais hardcoded;
- aprofundamento real do módulo `Lógica de Programação com Python` com base no livro do Nilo;
- modelagem negocial dos módulos `FastAPI`, `Vue`, `Integração Full-stack` e `OCP 17`;
- futura persistência editável e curadoria administrativa do catálogo sem deploy;
- ranking útil, separado de XP, apoiado nesse catálogo já consolidado.

Essas milestones estão detalhadas na KB, em [`kb/04_Milestones/Mapa de Milestones.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/04_Milestones/Mapa%20de%20Milestones.md).

## Produção

- domínio: [logic-arena.floresdev.com.br](https://logic-arena.floresdev.com.br)
- deploy: `GitHub Actions` + `SSH` na VPS
- health check público: [logic-arena.floresdev.com.br/api/health](https://logic-arena.floresdev.com.br/api/health)

## Princípios do projeto

- prática antes de abstração desnecessária;
- UX de prova sem perder apoio didático;
- feedback acionável em vez de correção opaca;
- documentação como parte do produto técnico;
- evolução incremental com arquitetura suficientemente clara.
