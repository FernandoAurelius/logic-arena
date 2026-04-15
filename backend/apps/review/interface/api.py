from ninja import Header, Router

from apps.accounts.application.services import require_session
from apps.review.application.services import (
    review_evaluation_chat_response,
    serialize_review_evaluation,
)
from apps.review.schemas import AIReviewSchema, ErrorSchema, EvaluationRunSchema, ReviewChatInputSchema, ReviewChatResponseSchema
from apps.review.selectors import get_ai_review_for_user, get_evaluation_run_for_user


evaluation_router = Router(tags=['review'])


@evaluation_router.get(
    '/evaluations/{evaluation_run_id}',
    response={200: EvaluationRunSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna o resultado objetivo de uma avaliação por evaluation run.',
)
def get_evaluation(request, evaluation_run_id: int, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    evaluation_run = get_evaluation_run_for_user(session.user, evaluation_run_id)
    if evaluation_run is None:
        return 404, {'message': 'Avaliação não encontrada.'}

    return 200, serialize_review_evaluation(evaluation_run)['evaluation']


@evaluation_router.get(
    '/evaluations/{evaluation_run_id}/review',
    response={200: AIReviewSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna a revisão ancorada na evaluation run.',
)
def get_evaluation_review(request, evaluation_run_id: int, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    review = get_ai_review_for_user(session.user, evaluation_run_id)
    if review is None:
        return 404, {'message': 'Revisão não encontrada.'}

    return 200, serialize_review_evaluation(review.evaluation_run)['review']
@evaluation_router.post(
    '/evaluations/{evaluation_run_id}/chat',
    response={200: ReviewChatResponseSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Continua a revisão com IA sobre uma evaluation run específica.',
)
def review_evaluation_chat(request, evaluation_run_id: int, payload: ReviewChatInputSchema, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    review = get_ai_review_for_user(session.user, evaluation_run_id)
    if review is None:
        return 404, {'message': 'Revisão não encontrada.'}

    persisted_history = review.conversation_thread or []
    answer = review_evaluation_chat_response(review.evaluation_run, payload.message, persisted_history)
    updated_history = [
        *persisted_history,
        {'role': 'user', 'content': payload.message},
        {'role': 'assistant', 'content': answer},
    ]
    review.conversation_thread = updated_history
    review.save(update_fields=['conversation_thread', 'updated_at'])
    return 200, {'answer': answer}
