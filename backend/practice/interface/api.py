from django.shortcuts import get_object_or_404
from ninja import Header, Router

from accounts.application.services import require_session
from practice.application.services import (
    evaluate_submission,
    review_submission_chat,
    serialize_exercise_detail,
    serialize_exercise_summary,
    serialize_submission,
    serialize_submission_summary,
)
from practice.selectors import get_submission_for_user, list_active_exercises, list_user_submissions
from practice.schemas import (
    ErrorSchema,
    ExerciseDetailSchema,
    ExerciseSummarySchema,
    ReviewChatInputSchema,
    ReviewChatResponseSchema,
    SubmissionInputSchema,
    SubmissionSchema,
    SubmissionSummarySchema,
)
from arena.models import Exercise


exercise_router = Router(tags=['exercises'])
submission_router = Router(tags=['submissions'])


@exercise_router.get('/', response={200: list[ExerciseSummarySchema], 401: ErrorSchema}, summary='Lista exercícios ativos.')
def list_exercises(request, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    return 200, [serialize_exercise_summary(exercise) for exercise in list_active_exercises()]


@exercise_router.get('/{slug}', response={200: ExerciseDetailSchema, 401: ErrorSchema}, summary='Detalha um exercício específico.')
def get_exercise(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    exercise = get_object_or_404(list_active_exercises().prefetch_related('test_cases'), slug=slug, is_active=True)
    return 200, serialize_exercise_detail(exercise)


@submission_router.post('/exercises/{slug}/submit', response={200: SubmissionSchema, 401: ErrorSchema}, summary='Executa os testes, persiste a submissão e devolve o resultado.')
def submit_exercise(request, slug: str, payload: SubmissionInputSchema, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    exercise = get_object_or_404(Exercise.objects.prefetch_related('test_cases'), slug=slug, is_active=True)
    submission, results = evaluate_submission(session.user, exercise, payload.source_code)
    serialized = serialize_submission(submission)
    serialized['results'] = results
    return 200, serialized


@submission_router.get('/me', response={200: list[SubmissionSummarySchema], 401: ErrorSchema}, summary='Lista as submissões do usuário autenticado.')
def list_my_submissions(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    return 200, [serialize_submission_summary(submission) for submission in list_user_submissions(session.user)]


@submission_router.get('/{submission_id}', response={200: SubmissionSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Retorna a submissão atualizada para polling do feedback.')
def get_submission(request, submission_id: int, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    submission = get_submission_for_user(session.user, submission_id)
    if submission is None:
        return 404, {'message': 'Submissão não encontrada.'}

    return 200, serialize_submission(submission)


@submission_router.post('/{submission_id}/review-chat', response={200: ReviewChatResponseSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Continua a revisão com IA sobre uma submissão específica.')
def review_chat(request, submission_id: int, payload: ReviewChatInputSchema, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    submission = get_submission_for_user(session.user, submission_id)
    if submission is None:
        return 404, {'message': 'Submissão não encontrada.'}

    persisted_history = submission.review_chat_history or []
    answer = review_submission_chat(
        exercise_title=submission.exercise.title,
        statement=submission.exercise.statement,
        source_code=submission.source_code,
        console_output=submission.console_output,
        feedback_summary=submission.feedback,
        user_message=payload.message,
        history=persisted_history,
    )
    updated_history = [
        *persisted_history,
        {'role': 'user', 'content': payload.message},
        {'role': 'assistant', 'content': answer},
    ]
    submission.review_chat_history = updated_history
    submission.save(update_fields=['review_chat_history', 'updated_at'])
    return 200, {'answer': answer}
