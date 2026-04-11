# Backend do Logic Arena

O backend do `Logic Arena` concentra a API principal do produto, persistência, contratos tipados e orquestração entre catálogo, submissão, execução e revisão com IA.

## Papel desta camada

Ele atua como o núcleo de aplicação do sistema:

- autentica o operador por `nickname + senha`;
- persiste exercícios e casos de teste;
- recebe submissões;
- delega execução ao `runner_service`;
- persiste o resultado da avaliação;
- dispara a revisão com IA em background;
- expõe um `OpenAPI` explícito para o frontend.

## Arquivos principais

- `arena/models.py`: domínio persistido do MVP
- `arena/api.py`: surface HTTP da aplicação
- `arena/services.py`: regras de sessão, criação de exercício, execução e avaliação
- `arena/feedback.py`: integração com `Agno + Gemini`
- `arena/migrations/0004_seed_professor_exercises.py`: seed inicial rico de exercícios
- `config/settings.py`: configuração do ambiente, banco, CORS e integração com IA

## Rodando localmente

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/backend"
.venv/bin/python -m pip install -e .
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo_exercises
.venv/bin/python manage.py export_openapi
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

## Dependências críticas

- `PostgreSQL` local em `127.0.0.1:5433` por padrão
- `RUNNER_URL` apontando para o serviço de execução
- `GEMINI_API_KEY` obrigatória

Sem `GEMINI_API_KEY`, o backend falha na inicialização por design.

## Health check

O endpoint público de saúde é:

- `GET /api/health`

## Leitura aprofundada

Para documentação didática e arquitetura desta camada, veja:

- [`kb/02_Bounded_Contexts/Autenticação e Sessão.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Autentica%C3%A7%C3%A3o%20e%20Sess%C3%A3o.md)
- [`kb/02_Bounded_Contexts/Catálogo de Exercícios.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Cat%C3%A1logo%20de%20Exerc%C3%ADcios.md)
- [`kb/02_Bounded_Contexts/Submissão, Runner e Correção.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Submiss%C3%A3o,%20Runner%20e%20Corre%C3%A7%C3%A3o.md)
- [`kb/02_Bounded_Contexts/Revisão com IA.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Revis%C3%A3o%20com%20IA.md)
