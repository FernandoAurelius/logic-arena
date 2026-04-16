from typing import Any

from django.conf import settings
from pydantic import BaseModel

from agno.agent import Agent
from agno.models.google import Gemini


class FeedbackPayload(BaseModel):
    summary: str
    strengths: list[str]
    issues: list[str]
    next_steps: list[str]
    source: str


def _format_project_files(project_files: dict[str, str] | None) -> str:
    if not project_files:
        return '(projeto com arquivo único ou sem arquivos auxiliares)'

    rendered_chunks: list[str] = []
    for file_name, content in project_files.items():
        rendered_chunks.append(
            '\n'.join(
                [
                    f'Arquivo: {file_name}',
                    '```python',
                    str(content),
                    '```',
                ]
            )
        )
    return '\n\n'.join(rendered_chunks)


def _build_agent() -> Agent:
    return Agent(
        model=Gemini(id=settings.AGNO_GEMINI_MODEL, api_key=settings.GEMINI_API_KEY),
        name='logic-arena-feedback',
        instructions=[
            'Você é um professor de lógica de programação extremamente didático.',
            'Analise soluções submetidas em Python com foco em clareza, correção, aderência ao enunciado e estilo de prova prática.',
            'Use os resultados dos testes como evidência principal.',
            'Seja objetivo, útil e acionável.',
            'Nunca invente erros que não estejam sustentados pelos resultados recebidos.',
        ],
        markdown=False,
    )


def build_agno_feedback(
    exercise_title: str,
    statement: str,
    source_code: str,
    project_files: dict[str, str] | None,
    passed_tests: int,
    total_tests: int,
    results: list[dict[str, Any]],
) -> FeedbackPayload:
    agent = Agent(
        model=Gemini(id=settings.AGNO_GEMINI_MODEL, api_key=settings.GEMINI_API_KEY),
        name='logic-arena-feedback-structured',
        instructions=[
            'Você é um professor de lógica de programação extremamente didático.',
            'Analise a solução submetida em Python com foco em clareza, correção, aderência ao enunciado e estilo de prova prática.',
            'Use os resultados dos testes como evidência principal.',
            'Seja objetivo, útil e acionável.',
            'Nunca invente erros que não estejam sustentados pelos resultados recebidos.',
        ],
        output_schema=FeedbackPayload,
        structured_outputs=True,
        markdown=False,
    )

    prompt = f"""
Exercício: {exercise_title}

Enunciado:
{statement}

Resultado dos testes: {passed_tests}/{total_tests}

Resultados detalhados:
{results}

Código submetido:
```python
{source_code}
```

Arquivos do projeto:
{_format_project_files(project_files)}

Gere um feedback curto, útil e acionável.
"""

    response = agent.run(prompt)
    content = response.content

    if isinstance(content, FeedbackPayload):
        return content.model_copy(update={'source': 'agno-gemini'})
    if isinstance(content, dict):
        payload = FeedbackPayload.model_validate(content)
        return payload.model_copy(update={'source': 'agno-gemini'})
    if isinstance(content, str):
        return FeedbackPayload(
            summary=content,
            strengths=['A IA identificou pontos positivos gerais da solução.'],
            issues=['Revise o resumo gerado pela IA para localizar a principal fragilidade da submissão.'],
            next_steps=['Ajuste a solução e submeta novamente para confirmar a melhora.'],
            source='agno-gemini',
        )

    raise RuntimeError('A integração com Gemini retornou um formato de resposta inesperado.')


def build_feedback_error_payload(error: Exception) -> FeedbackPayload:
    return FeedbackPayload(
        summary='A revisão automática com IA falhou temporariamente.',
        strengths=[],
        issues=[str(error)],
        next_steps=['Tente novamente em alguns instantes usando o botão de revisar com IA.'],
        source='agno-gemini',
    )


def review_submission_chat(
    exercise_title: str,
    statement: str,
    source_code: str,
    project_files: dict[str, str] | None,
    console_output: str,
    feedback_summary: str,
    user_message: str,
    history: list[dict[str, str]],
) -> str:
    agent = _build_agent()
    conversation = '\n'.join([f"{item['role']}: {item['content']}" for item in history]) if history else '(sem histórico anterior)'
    prompt = f"""
Exercício: {exercise_title}

Enunciado:
{statement}

Código submetido:
```python
{source_code}
```

Arquivos do projeto:
{_format_project_files(project_files)}

Console da avaliação:
{console_output}

Resumo do feedback atual:
{feedback_summary}

Histórico da conversa:
{conversation}

Pergunta do aluno:
{user_message}

Responda como um professor técnico, objetivo e didático. Explique o erro ou confirme o acerto com base no contexto recebido.
"""
    response = agent.run(prompt)
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, BaseModel):
        return str(content.model_dump())
    if isinstance(content, dict):
        return str(content)
    return 'Não foi possível interpretar a resposta da IA.'


def generate_feedback(
    exercise_title: str,
    statement: str,
    source_code: str,
    project_files: dict[str, str] | None,
    passed_tests: int,
    total_tests: int,
    results: list[dict[str, Any]],
) -> FeedbackPayload:
    return build_agno_feedback(
        exercise_title=exercise_title,
        statement=statement,
        source_code=source_code,
        project_files=project_files,
        passed_tests=passed_tests,
        total_tests=total_tests,
        results=results,
    )
