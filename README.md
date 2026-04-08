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
- resultado da execução devolvido imediatamente, com revisão por IA concluída em segundo plano
- feedback por IA sempre ativo via `Agno + Gemini`, com `GEMINI_API_KEY` obrigatório para o backend subir

## Estrutura atual

### Protótipo inicial

- `src/`
- `server.mjs`

Essa parte continua útil como referência de interação rápida e da arena prática original.

### MVP novo

- `backend/`: `Django Ninja`, agora com `PostgreSQL` como padrão real de desenvolvimento, modelos de usuário, sessão, exercício, casos de teste e submissão
- `backend/openapi.json`: schema exportado da API para geração do client tipado
- `frontend/`: `Vue 3 + TypeScript`, consumindo a API via `Zodios`, com camada de componentes no estilo `shadcn-vue` aplicada à arena principal e interface refeita para ficar fiel à linguagem visual da referência original
- `runner_service/`: microserviço `FastAPI` que executa o código Python e devolve `stdout/stderr/status` ao backend
- `docker-compose.yml`: stack local mínima com `PostgreSQL` e `runner`

## Como rodar o MVP novo

### Infra local

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app"
docker compose up -d postgres runner
```

O Postgres do projeto fica exposto em `127.0.0.1:5433`, para não colidir com outras instâncias locais em `5432`.

### Backend principal

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
.venv/bin/python -m pip install -e .
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo_exercises
.venv/bin/python manage.py export_openapi
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
- `GET /api/submissions/{id}`
- `POST /api/submissions/{id}/review-chat`

## Estado atual da rodada estrutural

- autenticação mínima com criação automática de usuário no `login`
- `OpenAPI` exportado pelo backend e consumido pelo frontend com `Zodios`
- `PostgreSQL` agora é o padrão real do setup local, rodando em `5433`
- `runner_service` já separado do backend principal
- feedback estruturado persistido em cada submissão, sempre vindo de `Agno + Gemini`
- UI refeita para ficar muito mais fiel ao idioma visual brutalista/técnico da referência original
- camada de componentes `shadcn-vue` aplicada de fato na estação principal (`Button`, `Card`, `Input`, `Textarea`, `Badge`, `ScrollArea`, `Separator`)
- `GEMINI_API_KEY` obrigatório em `backend/.env`; sem essa chave o backend falha na inicialização por design
- listagem e leitura de exercícios agora exigem autenticação válida; a arena não expõe mais conteúdo programático sem sessão
- o `Execution Canvas` voltou a ser um editor real com `Monaco`, usando tema customizado `Typewriter`
- a experiência de entrada foi separada em duas views: uma landing limpa em `/` e a arena autenticada em `/arena`, com login via modal e redirecionamento após a sessão
- a execução agora devolve a submissão imediatamente e o feedback com `Agno + Gemini` é finalizado em background, com polling na arena em vez de travar a estação até a IA responder
- a arena ganhou um botão `Revisar com IA`, que abre um chat curto sobre a última submissão para entender erro, raciocínio esperado e melhorias possíveis
- o cabeçalho pesado do `Execution Canvas` foi removido para devolver mais altura útil ao editor
- o corretor ficou semanticamente mais tolerante para saídas equivalentes em português, aceitando variações como `aprovado/passou` e `reprovado/reprovou` quando a intenção da resposta está correta
- a faixa inferior de gamificação antiga foi removida para simplificar a leitura, substituída por microinterações mais orgânicas: confete ao concluir com sucesso e um indicador de `forge heat` enquanto o usuário está digitando
- o bloco de `Submission` agora divide espaço com o chat de revisão em um grid de duas colunas, reduzindo ruído vertical na arena
- a revisão com IA saiu do fluxo central e virou um drawer lateral direito colapsável, deixando a leitura do exercício e do resultado principal mais limpa
- as respostas do drawer passaram a renderizar Markdown básico, incluindo blocos de código, e o painel agora abre/fecha de verdade com rolagem completa do conteúdo
- o bloco `History` da sidebar passou a ser colapsável e inicia fechado por padrão para reduzir ruído visual
- a navegação superior foi simplificada para reforçar o produto, usando apenas `LOGIC ARENA` como marca principal
- o projeto agora possui uma migration-seed rica em `backend/arena/migrations/0004_seed_professor_exercises.py`, gerando 26 exercícios baseados nas atividades reais do professor e nos scripts das aulas
- os materiais descompactados que serviram de base para esse seed ficaram organizados em `/home/miguelbarreto/estudos/logica-de-programacao/material-professor-downloads`
- a arena agora mantém um sistema mínimo de XP por operador, com persistência local por usuário, barra de progresso no topo e destaque visual quando acontece subida de nível

## Próximos passos naturais

- endurecer o consumo tipado do client gerado pelo `openapi-zod-client` sem depender do fallback leve atual em `frontend/src/lib/api/client.ts`
- adicionar autenticação de sessão mais durável e logout global
- criar fluxo programático de cadastro/edição de exercícios com autenticação interna
