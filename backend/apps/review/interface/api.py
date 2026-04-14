from ninja import Header, Router

from apps.accounts.application.services import require_session
from apps.review.application.services import review_submission_chat_response, serialize_review_submission
from apps.review.schemas import ErrorSchema, ReviewChatInputSchema, ReviewChatResponseSchema, SubmissionSchema
from apps.review.selectors import get_submission_for_user


router = Router(tags=['review'])


@router.get('/{submission_id}', response={200: SubmissionSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Retorna a submissão atualizada para polling do feedback.')
def get_submission(request, submission_id: int, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    submission = get_submission_for_user(session.user, submission_id)
    if submission is None:
        return 404, {'message': 'Submissão não encontrada.'}

    return 200, serialize_review_submission(submission)


@router.post('/{submission_id}/review-chat', response={200: ReviewChatResponseSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Continua a revisão com IA sobre uma submissão específica.')
def review_chat(request, submission_id: int, payload: ReviewChatInputSchema, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    submission = get_submission_for_user(session.user, submission_id)
    if submission is None:
        return 404, {'message': 'Submissão não encontrada.'}

    persisted_history = submission.review_chat_history or []
    answer = review_submission_chat_response(submission=submission, user_message=payload.message, history=persisted_history)
    updated_history = [
        *persisted_history,
        {'role': 'user', 'content': payload.message},
        {'role': 'assistant', 'content': answer},
    ]
    submission.review_chat_history = updated_history
    submission.save(update_fields=['review_chat_history', 'updated_at'])
    return 200, {'answer': answer}
