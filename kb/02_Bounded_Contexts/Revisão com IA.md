# Revisão com IA

## Objetivo do módulo

Transformar resultado de teste em explicação pedagógica acionável.

Sem essa camada, a plataforma continuaria útil como judge. Com ela, o produto começa a parecer uma estação de estudo real.

## Arquivos principais

- `backend/arena/feedback.py`
- `backend/arena/services.py`
- `backend/arena/api.py`
- `frontend/src/views/ArenaView.vue`

## Dois usos diferentes da IA

Hoje a IA participa em dois momentos:

1. revisão automática estruturada após a submissão;
2. chat contextual posterior sobre aquela mesma submissão.

Isso é importante porque o produto não trata IA como “resposta livre” genérica. A conversa sempre parte de um contexto técnico concreto:

- enunciado;
- código submetido;
- console da avaliação;
- resumo automático anterior;
- histórico de mensagens.

## Feedback estruturado

Trecho central:

```python
class FeedbackPayload(BaseModel):
    summary: str
    strengths: list[str]
    issues: list[str]
    next_steps: list[str]
    source: str
```

Esse contrato é importante porque obriga a IA a devolver algo consumível pelo produto, em vez de apenas um bloco de texto longo e difícil de reutilizar.

## Chat contextual

Depois da submissão, o usuário pode continuar perguntando:

- por que falhou;
- por que passou;
- como melhorar;
- como adaptar a solução ao padrão esperado.

Esse histórico é persistido em `review_chat_history`, o que transforma a revisão numa sessão restaurável.

## Leitura didática

Uma escolha central aqui foi tornar a IA obrigatória na inicialização do backend. Isso tem custo operacional, mas evita um problema comum: projetar produto com IA e, na prática, tratar IA como um anexo instável e opcional. O time preferiu o contrário: a revisão automática faz parte da definição do sistema.

## Tensões abertas

- ainda não há no backend distinção forte entre tipos de revisão;
- a UX do drawer pode continuar evoluindo;
- o produto ainda não separa bem revisão pedagógica, revisão de estilo e revisão arquitetural para desafios maiores.

## Por onde continuar

- [[Arena Frontend e Experiência]]
- [[../04_Milestones/M4 - Catálogo Avançado e Projetos Integradores]]
