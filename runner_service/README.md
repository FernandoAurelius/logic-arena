# Runner Service

O `runner_service` é a fronteira operacional que executa o código Python submetido pelo usuário fora do processo principal do backend.

## Por que ele existe

Sem esse isolamento, a API principal teria de executar código arbitrário no mesmo processo que gerencia autenticação, catálogo, submissões e revisão com IA. Mesmo em um MVP interno, isso mistura responsabilidades demais e dificulta evolução, observabilidade e endurecimento futuro.

## Responsabilidade atual

- receber `source_code`, `stdin` e `timeout_seconds`;
- opcionalmente receber `files` e `entrypoint` para workspaces multi-arquivo;
- materializar o workspace temporário em disco quando a tentativa for multifile;
- executar a solução em Python;
- devolver `stdout`, `stderr` e um status `ok`;
- responder rápido o suficiente para o backend montar a avaliação por caso de teste.

## Rodando localmente

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/runner_service"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8010
```

## Quando usar Docker

Para o fluxo principal do projeto, o caminho mais simples continua sendo:

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app"
docker compose up -d runner
```

## Leitura aprofundada

Para entender como o runner se conecta ao restante do sistema, leia:

- [`kb/02_Bounded_Contexts/Submissão, Runner e Correção.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Submiss%C3%A3o,%20Runner%20e%20Corre%C3%A7%C3%A3o.md)
- [`kb/03_Arquitetura/Visão Arquitetural.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/03_Arquitetura/Vis%C3%A3o%20Arquitetural.md)
