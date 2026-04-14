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

## 7. Bounded contexts como apps Django

### Decisão

O backend passa a tratar bounded contexts como apps em `backend/apps/*`.

### Justificativa

- deixa ownership mais claro;
- reduz service blob em um app único;
- aproxima o monólito de um dialeto pragmático de DDD compatível com Django.

### Regra prática

- `models.py`, `selectors.py`, `schemas.py`, `application/` e `interface/` existem por padrão;
- `domain/` só entra onde houver regra comportamental densa;
- `arena` fica como shell de integração, não como centro de domínio.

## 8. Frontend canônico em FSD

### Decisão

O frontend passa a tratar `shared`, `entities`, `features`, `widgets` e `pages` como camadas oficiais.

### Justificativa

- elimina áreas-curinga como `views/` e `components/`;
- melhora ownership de UI, tipos e fluxos de usuário;
- reduz regressão estrutural durante expansão do produto.

### Regra prática

- `src/views` e `src/components` não fazem mais parte do contrato;
- acesso ao gerado cru da API fica encapsulado;
- checks automáticos barram regressão de camadas.

## 9. Boy Scout Rule como regra permanente

### Decisão

Sempre que possível, mudanças no `Logic Arena` devem aplicar a `Boy Scout Rule`.

### Justificativa

- evita regressão silenciosa enquanto o produto cresce;
- reduz a tendência de conviver com duplicação, acoplamento ruim e organização frouxa;
- transforma polimento arquitetural em parte do fluxo normal de evolução, e não em fase rara e pesada.

### Regra prática

- aplicar melhorias pequenas e seguras de `SOLID`, `DRY` e organização quando elas estiverem claramente ao alcance da mudança em curso;
- empurrar código para a camada correta quando o desalinhamento for evidente;
- não usar essa regra como desculpa para rewrites oportunistas ou refactors desproporcionais ao escopo.

## Leituras seguintes

- [[../04_Milestones/Mapa de Milestones]]
- [[../05_Agentes/Playbook de Implementação com Subagentes]]
