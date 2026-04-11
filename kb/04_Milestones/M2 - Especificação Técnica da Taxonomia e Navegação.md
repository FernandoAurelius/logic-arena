# M2 - Especificação Técnica da Taxonomia e Navegação

## Objetivo desta nota

Traduzir a `M2` em uma sequência implementável e em um escopo fechável.

## O que já está pronto na base

Hoje o sistema já possui:

- `ExerciseCategory`
- `ExerciseTrack`
- `Exercise.category`
- `Exercise.track`
- seed inicial com classificação do catálogo
- API retornando `category_*` e `track_*`
- agrupamento visual por categoria na sidebar

Isso é uma boa fundação, mas ainda não é a solução completa da milestone.

## O que falta para a M2 ficar “de pé”

### 1. Navegação explícita por taxonomia

Hoje a arena só agrupa exercícios por categoria. Falta transformar isso numa navegação realmente orientada à taxonomia.

Isso pode ser feito com uma destas abordagens:

#### Abordagem A — rail hierárquico

- categoria como cabeçalho
- trilhas como subgrupos colapsáveis
- exercícios dentro de cada trilha

#### Abordagem B — filtros + lista

- filtro por categoria
- filtro por trilha
- lista de exercícios refinada dinamicamente

#### Recomendação

Para o estado atual do produto, eu adotaria um híbrido:

- agrupamento hierárquico na lateral
- filtros leves no topo do catálogo

Isso preserva simplicidade e já melhora muito a descoberta.

## 2. Metadados mínimos adicionais no domínio

Para a navegação deixar de ser apenas estrutural e passar a ser pedagógica, o modelo deveria ganhar ao menos:

### `exercise_type`

Valores possíveis na primeira versão:

- `exam_like`
- `practice`
- `integrative`

### `estimated_time_minutes`

Ajuda a comunicar tamanho do esforço e prepara melhor a gamificação/planejamento.

### `sort_order`

Dentro da trilha, a ordem não deve depender só do título.

### `is_recommended_start`

Opcional, mas muito útil para trilhas com ponto de entrada claro.

## 3. API mais adequada para navegação

Hoje a API já devolve taxonomia embutida por exercício. Isso é bom, mas ainda insuficiente para uma navegação canônica madura.

### Evoluções recomendadas

#### Opção mínima

Adicionar filtros em `GET /api/exercises/`:

- `category_slug`
- `track_slug`
- `difficulty`

#### Opção melhor

Criar também um endpoint de catálogo estruturado, como:

- `GET /api/exercise-catalog`

Resposta sugerida:

```json
[
  {
    "category_slug": "fundamentos",
    "category_name": "Fundamentos",
    "tracks": [
      {
        "track_slug": "condicionais-basicas",
        "track_name": "Condicionais Básicas",
        "exercise_count": 8,
        "exercises": [...]
      }
    ]
  }
]
```

### Recomendação

Para fechar a `M2` com elegância, o endpoint de catálogo estruturado é melhor do que depender só de agrupamento no frontend.

## 4. UX alvo para fechamento adequado da M2

Uma `M2` bem concluída precisa permitir que o usuário:

- veja categorias e trilhas com clareza;
- entenda a posição do exercício atual no mapa;
- filtre rapidamente o catálogo;
- saiba qual trilha está fazendo;
- perceba o próximo passo natural.

## 5. Checklist de fechamento realista

### Backend

- modelos com taxonomia mínima estável
- seed todo classificado
- nenhum exercício órfão
- filtros no endpoint ou catálogo estruturado

### Frontend

- navegação por categoria e trilha
- filtros básicos
- estado visual do exercício atual dentro da trilha
- caminho sugerido de progressão

### Conteúdo

- taxonomia revisada com coerência pedagógica
- ordem dos exercícios definida dentro de cada trilha

## 6. O que eu considero “fora da M2”

Para não inflar a milestone além do necessário, eu não colocaria aqui:

- achievements
- ranking
- mastery scoring
- badges
- desafios full-stack

Esses pontos dependem da `M2`, mas pertencem a outras milestones.

## Sequência recomendada para completar a M2

1. adicionar metadados mínimos faltantes no domínio
2. expor filtro/catálogo estruturado na API
3. refazer a navegação lateral para categoria + trilha
4. adicionar filtros básicos
5. comunicar ordem recomendada de progressão
6. revisar seed e classificação final

## Conclusão operacional

Se a pergunta é “o que falta para a tarefa estar realmente concluída no escopo da `M2`?”, a resposta curta é:

**falta transformar taxonomia em navegação pedagógica de verdade**.

Hoje a taxonomia existe. O que ainda não existe plenamente é a experiência canônica baseada nela.
