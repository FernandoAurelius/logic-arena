# Decisões Arquiteturais

## 1. Backend em Django Ninja

### Decisão

Usar `Django + Django Ninja` como núcleo da API.

### Justificativa

- entrega ORM, migrations e admin implícito se necessário;
- reduz fricção para evoluir o domínio;
- `Django Ninja` permite surface HTTP moderna com schema explícito.

### Tradeoff

- carrega mais estrutura do que uma micro-API minimalista;
- algumas áreas do domínio ainda estão simples demais para aproveitar tudo que Django pode oferecer.

## 2. Execução isolada em serviço separado

### Decisão

Executar código no `runner_service`, não no backend principal.

### Justificativa

- separa avaliação de aplicação;
- evita misturar código arbitrário com sessão, catálogo e IA;
- prepara terreno para limites de tempo e políticas mais rígidas.

## 3. Feedback com IA obrigatório

### Decisão

O backend só sobe com `GEMINI_API_KEY`.

### Justificativa

- a revisão com IA foi tratada como parte do produto, não como extra opcional;
- isso força o sistema local e produtivo a refletirem o fluxo real.

### Tradeoff

- aumenta acoplamento operacional com provedor externo;
- encarece o setup local.

## 4. Login mínimo com criação automática

### Decisão

Não há cadastro separado. `POST /auth/login` cria o usuário caso ele ainda não exista.

### Justificativa

- reduz fricção para um produto pequeno e interno;
- acelera o uso em contexto de turma/equipe.

### Tradeoff

- serve para ambiente restrito, mas não é desenho final de produto público.

## 5. Histórico restaurável como memória pedagógica

### Decisão

Ao reabrir uma submissão, restaurar código, console, feedback e chat.

### Justificativa

- treino bom depende de revisar o próprio raciocínio;
- o valor da plataforma aumenta muito quando a sessão não morre ao final do clique.

## 6. KB dentro do repositório

### Decisão

Manter uma knowledge base orientada a Obsidian dentro do próprio repo.

### Justificativa

- aproxima documentação de código e milestone;
- facilita trabalho com agentes;
- torna a arquitetura e o roadmap parte viva do projeto.

## Leituras seguintes

- [[../04_Milestones/Mapa de Milestones]]
- [[../05_Agentes/Playbook de Implementação com Subagentes]]
