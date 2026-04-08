# Logic Arena

Repositório da evolução do simulador de prova prática de Lógica de Programação.

Hoje ele tem duas camadas:

- um protótipo local em `React/Vite` na raiz, criado para calibrar UX, editor e correção prática rapidamente
- uma base de MVP em `backend/` + `frontend/`, já alinhada com a stack alvo: `Django Ninja` no backend e `Vue 3 + TypeScript` no frontend, com contrato `OpenAPI` explícito e geração de client tipado para `Zodios`
- um `runner_service/` isolado para execução de código Python fora do processo principal do backend

## Direção do produto

O `Logic Arena` quer ser uma estação simples de treino interno para colegas praticarem exatamente o estilo de avaliação prática cobrado em aula:

- autenticação mínima por `nickname + senha`
- criação automática do usuário no primeiro login
- exercícios persistidos em banco
- cadastro de novos exercícios via API, sem painel administrativo
- submissões salvas por exercício
- feedback básico imediato após a correção
- base pronta para futura integração com IA via `Agno`

## Estrutura atual

### Protótipo inicial

- `src/`
- `server.mjs`

Essa parte continua útil como referência de interação rápida e da arena prática original.

### MVP novo

- `backend/`: `Django Ninja`, já preparado para `PostgreSQL`, com modelos de usuário, sessão, exercício, casos de teste e submissão
- `backend/openapi.json`: schema exportado da API para geração do client tipado
- `frontend/`: `Vue 3 + TypeScript`, consumindo a API via `Zodios`, com interface refeita para ficar fiel à linguagem visual da referência original
- `runner_service/`: microserviço `FastAPI` que executa o código Python e devolve `stdout/stderr/status` ao backend
- `docker-compose.yml`: stack local mínima com `PostgreSQL` e `runner`

## Como rodar o MVP novo

### Infra local

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app"
docker compose up -d postgres runner
```

### Backend principal

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
.venv/bin/python -m pip install -e .
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo_exercises
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

### Frontend

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/frontend"
npm install
npm run generate:api
npm run dev
```

Se quiser apontar o frontend para outro host da API:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

### Runner isolado sem Docker

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/runner_service"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8010
```

## Endpoints iniciais do MVP

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/exercises/`
- `GET /api/exercises/{slug}`
- `POST /api/exercises/`
- `POST /api/submissions/exercises/{slug}/submit`
- `GET /api/submissions/me`

## Estado atual da rodada estrutural

- autenticação mínima com criação automática de usuário no `login`
- `OpenAPI` exportado pelo backend e consumido pelo frontend com `Zodios`
- `PostgreSQL` já preparado via configuração por ambiente e `docker-compose`
- `runner_service` já separado do backend principal
- UI refeita para ficar muito mais fiel ao idioma visual brutalista/técnico da referência original

## Próximos passos naturais

- trocar o ambiente local padrão de `SQLite` para `PostgreSQL` em todas as execuções de desenvolvimento
- adicionar feedback com `Agno`
- evoluir a UI atual para componentes `shadcn-vue`
- criar fluxo programático de cadastro/edição de exercícios com autenticação interna
