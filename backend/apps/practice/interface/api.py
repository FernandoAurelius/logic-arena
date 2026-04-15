from ninja import Header, Router

from apps.accounts.application.services import require_session
from apps.catalog.application.services import create_exercise
from apps.arena.models import AttemptSession, Exercise
from apps.arena.schemas import ExerciseCreateSchema
from apps.practice.application.services import (
    build_session_config,
    create_attempt_session_for_assessment,
    create_attempt_session_for_exercise,
    evaluate_attempt_session,
    serialize_assessment_container,
    serialize_attempt_session,
    serialize_exercise_detail,
    serialize_exercise_summary,
    serialize_submission_snapshot,
    update_attempt_session_state,
)
from apps.practice.selectors import (
    get_active_assessment_by_slug,
    get_active_exercise_by_slug,
    list_active_exercises,
    list_user_attempt_sessions,
)
from apps.practice.schemas import (
    AssessmentContainerSchema,
    AttemptEvaluationResponseSchema,
    AttemptSessionSchema,
    AttemptSessionPatchSchema,
    ErrorSchema,
    ExerciseDetailSchema,
    ExerciseSummarySchema,
    PracticeAnswerInputSchema,
    SessionConfigSchema,
)


practice_router = Router(tags=['practice'])
assessment_router = Router(tags=['assessments'])


@practice_router.get('/exercises', response={200: list[ExerciseSummarySchema], 401: ErrorSchema}, summary='Lista exercícios ativos disponíveis para prática.')
def list_exercises(request, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    return 200, [serialize_exercise_summary(exercise) for exercise in list_active_exercises()]


@practice_router.get('/exercises/{slug}', response={200: ExerciseDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Detalha um exercício específico.')
def get_exercise(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    exercise = get_active_exercise_by_slug(slug)
    if exercise is None:
        return 404, {'message': 'Exercício não encontrado.'}

    return 200, serialize_exercise_detail(exercise)


@practice_router.post('/exercises', response={201: ExerciseDetailSchema, 400: ErrorSchema, 401: ErrorSchema}, summary='Cadastra um exercício novo via API canônica.')
def post_exercise(request, payload: ExerciseCreateSchema, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    if Exercise.objects.filter(slug=payload.slug).exists():
        return 400, {'message': 'Já existe um exercício com esse slug.'}

    try:
        exercise = create_exercise(payload)
    except ValueError as error:
        return 400, {'message': str(error)}
    return 201, serialize_exercise_detail(exercise)


@practice_router.get(
    '/exercises/{slug}/session-config',
    response={200: SessionConfigSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna a configuração da sessão de prática para um exercício.',
)
def get_exercise_session_config(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    exercise = get_active_exercise_by_slug(slug)
    if exercise is None:
        return 404, {'message': 'Exercício não encontrado.'}

    return 200, build_session_config(exercise)


@practice_router.post(
    '/exercises/{slug}/sessions',
    response={201: AttemptSessionSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Abre uma nova sessão de prática para um exercício.',
)
def create_exercise_session(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    exercise = get_active_exercise_by_slug(slug)
    if exercise is None:
        return 404, {'message': 'Exercício não encontrado.'}

    attempt_session = create_attempt_session_for_exercise(session.user, exercise)
    return 201, serialize_attempt_session(attempt_session)


@practice_router.get(
    '/sessions',
    response={200: list[AttemptSessionSchema], 401: ErrorSchema},
    summary='Lista o histórico canônico de sessões do usuário autenticado.',
)
def list_practice_sessions(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    attempt_sessions = list_user_attempt_sessions(session.user)
    return 200, [serialize_attempt_session(attempt_session) for attempt_session in attempt_sessions]


@practice_router.get(
    '/sessions/{session_id}',
    response={200: AttemptSessionSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna uma sessão de prática existente.',
)
def get_practice_session(request, session_id: int, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    attempt_session = AttemptSession.objects.select_related('exercise', 'assessment').filter(id=session_id, user=session.user).first()
    if attempt_session is None:
        return 404, {'message': 'Sessão não encontrada.'}

    return 200, serialize_attempt_session(attempt_session)


@practice_router.patch(
    '/sessions/{session_id}',
    response={200: AttemptSessionSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Atualiza o estado local da sessão.',
)
def patch_practice_session(
    request,
    session_id: int,
    payload: AttemptSessionPatchSchema,
    authorization: str | None = Header(default=None),
):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    attempt_session = AttemptSession.objects.filter(id=session_id, user=session.user).first()
    if attempt_session is None:
        return 404, {'message': 'Sessão não encontrada.'}

    updated = update_attempt_session_state(
        attempt_session,
        state=payload.state,
        current_workspace_state=payload.current_workspace_state,
        answer_state=payload.answer_state,
    )
    return 200, serialize_attempt_session(updated)


def _evaluate_practice_session(session_id: int, snapshot_type: str, payload: PracticeAnswerInputSchema, authorization: str | None):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    attempt_session = AttemptSession.objects.select_related('exercise', 'assessment').filter(id=session_id, user=session.user).first()
    if attempt_session is None:
        return 404, {'message': 'Sessão não encontrada.'}

    try:
        snapshot, evaluation_run, review, _legacy_submission = evaluate_attempt_session(
            attempt_session,
            snapshot_type=snapshot_type,
            source_code=payload.source_code,
            selected_options=payload.selected_options,
            response_text=payload.response_text,
            files=payload.files,
        )
    except ValueError as error:
        return 400, {'message': str(error)}
    serialized_session = serialize_attempt_session(attempt_session)
    return 200, {
        'session': serialized_session,
        'snapshot': serialize_submission_snapshot(snapshot),
        'evaluation': serialized_session.get('latest_evaluation'),
        'review': serialized_session.get('latest_review') if review else None,
        'xp_awarded': serialized_session.get('xp_awarded', 0),
        'unlocked_progress_rewards': serialized_session.get('unlocked_progress_rewards', []),
        'exercise_progress': serialized_session.get('exercise_progress'),
        'user_progress': serialized_session.get('user_progress'),
    }


@practice_router.post(
    '/sessions/{session_id}/run',
    response={200: AttemptEvaluationResponseSchema, 400: ErrorSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Executa um run intermediário dentro da sessão.',
)
def run_practice_session(request, session_id: int, payload: PracticeAnswerInputSchema, authorization: str | None = Header(default=None)):
    return _evaluate_practice_session(session_id, 'run', payload, authorization)


@practice_router.post(
    '/sessions/{session_id}/check',
    response={200: AttemptEvaluationResponseSchema, 400: ErrorSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Executa uma checagem estruturada dentro da sessão.',
)
def check_practice_session(request, session_id: int, payload: PracticeAnswerInputSchema, authorization: str | None = Header(default=None)):
    return _evaluate_practice_session(session_id, 'check', payload, authorization)


@practice_router.post(
    '/sessions/{session_id}/submit',
    response={200: AttemptEvaluationResponseSchema, 400: ErrorSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Submete a sessão de prática e gera avaliação persistida.',
)
def submit_practice_session(request, session_id: int, payload: PracticeAnswerInputSchema, authorization: str | None = Header(default=None)):
    return _evaluate_practice_session(session_id, 'submit', payload, authorization)


@assessment_router.get(
    '/{slug}',
    response={200: AssessmentContainerSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna o detalhe de um assessment container ativo.',
)
def get_assessment(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    assessment = get_active_assessment_by_slug(slug)
    if assessment is None:
        return 404, {'message': 'Assessment não encontrado.'}

    return 200, serialize_assessment_container(assessment)


@assessment_router.post(
    '/{slug}/sessions',
    response={201: AttemptSessionSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Abre uma nova sessão para um assessment container.',
)
def create_assessment_session(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    assessment = get_active_assessment_by_slug(slug)
    if assessment is None:
        return 404, {'message': 'Assessment não encontrado.'}

    attempt_session = create_attempt_session_for_assessment(session.user, assessment)
    return 201, serialize_attempt_session(attempt_session)
