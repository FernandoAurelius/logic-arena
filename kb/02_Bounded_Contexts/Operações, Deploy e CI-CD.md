# Operações, Deploy e CI-CD

## Objetivo do módulo

Explicar como o produto sai do laptop e vira serviço disponível com previsibilidade.

## Arquivos principais

- `.github/workflows/deploy.yml`
- `docker-compose.yml`
- `backend/config/settings.py`

## Produção atual

- domínio: `logic-arena.floresdev.com.br`
- backend servido com `gunicorn`
- frontend buildado e servido por `Nginx`
- runner isolado separado
- banco em `PostgreSQL`

## Pipeline atual

O workflow de deploy faz:

```yaml
- git fetch origin
- git reset --hard origin/main
- manage.py migrate
- manage.py check
- manage.py export_openapi
- restart do backend
- build do frontend
- rsync do dist
- nginx -t
- health check público
```

Esse desenho é suficiente para o estágio atual porque privilegia legibilidade operacional. Não há ainda estratégias como rollback automatizado, blue/green ou smoke tests mais ricos, mas o pipeline já fecha o ciclo mínimo de entrega com segurança razoável.

## Leitura didática

Um detalhe importante é que o CI/CD foi desenhado para verificar o sistema que realmente está no ar, e não apenas completar etapas locais de build. O `health check` final contra o domínio público ajuda a evitar falso positivo de deploy.

## Tensões abertas

- não há rollback automático;
- não há deploy seletivo por área alterada;
- a pipeline ainda não formaliza observabilidade além do health check.

## Por onde continuar

- [[../04_Milestones/Mapa de Milestones]]
