# Logic Arena

Repositório da evolução do simulador de prova prática de Lógica de Programação.

Hoje ele tem duas camadas:

- um protótipo local em `React/Vite` na raiz, criado para calibrar UX, editor e correção prática rapidamente
- uma base de MVP em `backend/` + `frontend/`, já alinhada com a stack alvo: `Django Ninja` no backend e `Vue 3 + TypeScript` no frontend, com contrato `OpenAPI` explícito e geração de client tipado para `Zodios`

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

- `backend/`: `Django Ninja`, `SQLite` por enquanto, modelos de usuário, sessão, exercício, casos de teste e submissão
- `backend/openapi.json`: schema exportado da API para geração do client tipado
- `frontend/`: `Vue 3 + TypeScript`, consumindo a API via `Zodios`

## Como rodar o MVP novo

### Backend

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
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

## Endpoints iniciais do MVP

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/exercises/`
- `GET /api/exercises/{slug}`
- `POST /api/exercises/`
- `POST /api/submissions/exercises/{slug}/submit`
- `GET /api/submissions/me`

## Próximos passos naturais

- trocar `SQLite` por `PostgreSQL`
- isolar o runner Python em serviço próprio
- adicionar feedback com `Agno`
- evoluir a UI para uma base mais completa em `shadcn-vue`
