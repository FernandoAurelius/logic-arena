# Catálogo de Exercícios

## Objetivo do módulo

Este contexto organiza a matéria-prima do produto: os exercícios. Sem ele, a arena vira só um editor com runner. Com ele, o sistema ganha conteúdo, progressão possível e identidade pedagógica.

## Arquivos principais

- `backend/arena/models.py`
- `backend/arena/api.py`
- `backend/arena/services.py`
- `backend/arena/migrations/0004_seed_professor_exercises.py`

## Modelo atual

Hoje `Exercise` ainda é relativamente plano:

```python
class Exercise(TimestampedModel):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=140)
    statement = models.TextField()
    difficulty = models.CharField(max_length=20, default='iniciante')
    language = models.CharField(max_length=20, default='python')
    starter_code = models.TextField(blank=True)
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    professor_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

Há também `ExerciseTestCase`, que separa entrada, saída esperada e visibilidade do caso.

## O que esse modelo já resolve

- cadastro via API;
- seed inicial rico via migration;
- testes visíveis e ocultos;
- exemplos de entrada e saída;
- nota do professor como contexto pedagógico adicional.

## O que ele ainda não resolve

Ele não carrega taxonomia suficiente para um catálogo maior. Hoje faltam conceitos como:

- categoria;
- assunto;
- subassunto;
- trilha;
- tempo estimado;
- tipo de desafio;
- pré-requisitos;
- objetivos de aprendizagem.

Sem isso, a navegação tende a ficar ruim conforme o número de exercícios cresce.

## Seed atual

A migration `0004_seed_professor_exercises.py` é importante porque marca uma transição do produto: o catálogo deixa de ser apenas demo e passa a se apoiar em materiais reais do professor.

Trecho de exemplo:

```python
{
    'slug': 'media-duas-notas',
    'title': 'Média de Duas Notas',
    'statement': 'Leia duas notas, calcule a média aritmética...',
    'difficulty': 'iniciante',
    'language': 'python',
    'professor_note': 'Baseado em l03e02calcula_media_aula.py...',
}
```

## Leitura didática

O catálogo atual é forte para treino de prova básica porque deriva de exercícios reais de sala. Isso dá aderência pedagógica. Ao mesmo tempo, revela o próximo gargalo do produto: a necessidade de passar de lista de exercícios para sistema de trilhas.

## Tensões abertas

- o `starter_code` ainda existe no modelo, embora hoje fique escondido por hints;
- o seed está rico em fundamentos, mas ainda pouco diverso em tipos de desafio;
- a ausência de taxonomia dificulta ranking por domínio e navegação mais inteligente.

## Por onde continuar

- [[Submissão, Runner e Correção]]
- [[../04_Milestones/M2 - Taxonomia e Navegação Canônica]]
- [[../04_Milestones/M4 - Catálogo Avançado e Projetos Integradores]]
