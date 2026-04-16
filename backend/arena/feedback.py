import json
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


def _build_agent() -> Agent:
    return Agent(
        model=Gemini(id=settings.AGNO_GEMINI_MODEL, api_key=settings.GEMINI_API_KEY),
        name='logic-arena-feedback',
        instructions=[
            'Você é um professor de lógica de programação extremamente didático.',
            'Analise a tentativa submetida com foco em clareza, correção, aderência ao enunciado e evidências objetivas.',
            'Use os resultados, o contrato esperado e o contexto estruturado como evidência principal.',
            'Seja objetivo, útil e acionável.',
            'Nunca invente erros que não estejam sustentados pelos resultados recebidos.',
        ],
        markdown=False,
    )


def build_agno_feedback(
    exercise_title: str,
    statement: str,
    source_code: str,
    passed_tests: int,
    total_tests: int,
    results: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
) -> FeedbackPayload:
    agent = Agent(
        model=Gemini(id=settings.AGNO_GEMINI_MODEL, api_key=settings.GEMINI_API_KEY),
        name='logic-arena-feedback-structured',
        instructions=[
            'Você é um professor de lógica de programação extremamente didático.',
            'Analise a tentativa submetida com foco em clareza, correção, aderência ao enunciado e evidências objetivas.',
            'Use os resultados, o contrato esperado e o contexto estruturado como evidência principal.',
            'Seja objetivo, útil e acionável.',
            'Nunca invente erros que não estejam sustentados pelos resultados recebidos.',
        ],
        output_schema=FeedbackPayload,
        structured_outputs=True,
        markdown=False,
    )

    context_block = json.dumps(context or {}, ensure_ascii=False, indent=2, default=str)
    prompt = f"""
Exercício: {exercise_title}

Enunciado:
{statement}

Resultado dos testes: {passed_tests}/{total_tests}

Resultados detalhados:
{results}

Artefato submetido:
```text
{source_code}
```

Contexto estruturado:
{context_block}

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
    console_output: str,
    feedback_summary: str,
    user_message: str,
    history: list[dict[str, str]],
    context: dict[str, Any] | None = None,
) -> str:
    agent = _build_agent()
    conversation = '\n'.join([f"{item['role']}: {item['content']}" for item in history]) if history else '(sem histórico anterior)'
    context_block = json.dumps(context or {}, ensure_ascii=False, indent=2, default=str)
    prompt = f"""
Exercício: {exercise_title}

Enunciado:
{statement}

Artefato submetido:
```text
{source_code}
```

Console da avaliação:
{console_output}

Resumo do feedback atual:
{feedback_summary}

Histórico da conversa:
{conversation}

Contexto estruturado:
{context_block}

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
    passed_tests: int,
    total_tests: int,
    results: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
) -> FeedbackPayload:
    return build_agno_feedback(
        exercise_title=exercise_title,
        statement=statement,
        source_code=source_code,
        passed_tests=passed_tests,
        total_tests=total_tests,
        results=results,
        context=context,
    )
