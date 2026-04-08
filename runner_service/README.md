# Runner Service

Serviço isolado de execução usado pelo backend principal do Logic Arena.

## Rodando localmente

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/runner_service"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8010
```
