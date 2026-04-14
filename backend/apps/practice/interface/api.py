from django.shortcuts import get_object_or_404
from ninja import Header, Router

from apps.accounts.application.services import require_session
from apps.catalog.application.services import create_exercise
from apps.practice.application.services import (
    evaluate_submission,
    serialize_exercise_detail,
    serialize_exercise_summary,
    serialize_submission,
    serialize_submission_summary,
)
from apps.practice.selectors import list_active_exercises, list_user_submissions
from apps.practice.schemas import (
    ErrorSchema,
    ExerciseDetailSchema,
    ExerciseSummarySchema,
    SubmissionInputSchema,
    SubmissionSchema,
    SubmissionSummarySchema,
)
from apps.arena.models import Exercise
from apps.arena.schemas import ExerciseCreateSchema


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


@exercise_router.post('/', response={201: ExerciseDetailSchema, 400: ErrorSchema, 401: ErrorSchema}, summary='Cadastra um exercício novo via API.')
def post_exercise(request, payload: ExerciseCreateSchema, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    if Exercise.objects.filter(slug=payload.slug).exists():
        return 400, {'message': 'Já existe um exercício com esse slug.'}

    exercise = create_exercise(payload)
    return 201, serialize_exercise_detail(exercise)


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
