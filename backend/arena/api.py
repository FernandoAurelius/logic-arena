from django.shortcuts import get_object_or_404
from ninja import Header, NinjaAPI, Router

from .models import AuthSession, Exercise, Submission, UserExerciseProgress
from .schemas import (
    ErrorSchema,
    ExerciseCreateSchema,
    ExerciseDetailSchema,
    ExerciseSummarySchema,
    ReviewChatInputSchema,
    ReviewChatResponseSchema,
    LoginInputSchema,
    LoginResponseSchema,
    SubmissionInputSchema,
    SubmissionSchema,
    SubmissionSummarySchema,
    UserSchema,
)
from .feedback import review_submission_chat
from .services import (
    build_exercise_progress_payload,
    build_user_progress_summary,
    build_user_schema_payload,
    create_exercise,
    evaluate_submission,
    get_or_create_session,
)


api = NinjaAPI(
    title='Logic Arena API',
    version='0.1.0',
    description='API do MVP do Logic Arena com autenticação simples, exercícios persistidos e submissões avaliadas.',
    urls_namespace='logic_arena_api',
)

auth_router = Router(tags=['auth'])
exercise_router = Router(tags=['exercises'])
submission_router = Router(tags=['submissions'])
system_router = Router(tags=['system'])


def require_session(authorization: str | None) -> AuthSession:
    if not authorization or not authorization.startswith('Bearer '):
        raise PermissionError('Token ausente ou inválido.')
    token = authorization.replace('Bearer ', '', 1).strip()
    session = AuthSession.objects.select_related('user').filter(token=token).first()
    if session is None:
        raise PermissionError('Sessão não encontrada.')
    return session


def serialize_submission(submission: Submission) -> dict:
    progress = UserExerciseProgress.objects.filter(user=submission.user, exercise=submission.exercise).first()
    return {
        'id': submission.id,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'source_code': submission.source_code,
        'console_output': submission.console_output,
        'feedback': submission.feedback,
        'feedback_status': submission.feedback_status,
        'feedback_source': submission.feedback_source,
        'feedback_payload': submission.feedback_payload,
        'review_chat_history': submission.review_chat_history,
        'created_at': submission.created_at,
        'results': submission.execution_results,
        'xp_awarded': submission.xp_awarded,
        'unlocked_progress_rewards': submission.unlocked_progress_rewards,
        'exercise_progress': build_exercise_progress_payload(progress) if progress else {
            'attempts_count': 0,
            'best_passed_tests': 0,
            'best_total_tests': 0,
            'best_ratio': 0,
            'xp_awarded_total': 0,
            'first_passed_at': None,
            'awarded_progress_markers': [],
        },
        'user_progress': build_user_progress_summary(submission.user),
    }


def serialize_exercise_summary(exercise: Exercise) -> dict:
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
        'category_slug': exercise.category.slug if exercise.category else None,
        'category_name': exercise.category.name if exercise.category else None,
        'track_slug': exercise.track.slug if exercise.track else None,
        'track_name': exercise.track.name if exercise.track else None,
    }


@auth_router.post('/login', response={200: LoginResponseSchema, 401: ErrorSchema}, summary='Faz login ou cria o usuário automaticamente.')
def login(request, payload: LoginInputSchema):
    try:
        session, created = get_or_create_session(payload.nickname.strip(), payload.password)
    except ValueError as error:
        return 401, {'message': str(error)}

    return 200, {
        'token': session.token,
        'created': created,
        'user': build_user_schema_payload(session.user),
    }


@system_router.get('/health', summary='Health check público da API.')
def health(request):
    return 200, {'status': 'ok'}


@auth_router.get('/me', response={200: UserSchema, 401: ErrorSchema}, summary='Retorna o usuário autenticado.')
def me(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    return 200, build_user_schema_payload(session.user)


@exercise_router.get('/', response={200: list[ExerciseSummarySchema], 401: ErrorSchema}, summary='Lista exercícios ativos.')
def list_exercises(request, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    exercises = Exercise.objects.filter(is_active=True).select_related('category', 'track')
    return 200, [serialize_exercise_summary(exercise) for exercise in exercises]


@exercise_router.get('/{slug}', response={200: ExerciseDetailSchema, 401: ErrorSchema}, summary='Detalha um exercício específico.')
def get_exercise(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    exercise = get_object_or_404(Exercise.objects.prefetch_related('test_cases').select_related('category', 'track'), slug=slug, is_active=True)
    return 200, {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'test_cases': list(exercise.test_cases.filter(is_hidden=False)),
    }


@exercise_router.post('/', response={201: ExerciseDetailSchema, 400: ErrorSchema, 401: ErrorSchema}, summary='Cadastra um exercício novo via API.')
def post_exercise(request, payload: ExerciseCreateSchema, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    if Exercise.objects.filter(slug=payload.slug).exists():
        return 400, {'message': 'Já existe um exercício com esse slug.'}

    exercise = create_exercise(payload)
    return 201, {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'test_cases': list(exercise.test_cases.all()),
    }


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

    return 200, [
        {
            'id': submission.id,
            'exercise_slug': submission.exercise.slug,
            'exercise_title': submission.exercise.title,
            'status': submission.status,
            'passed_tests': submission.passed_tests,
            'total_tests': submission.total_tests,
            'feedback_status': submission.feedback_status,
            'feedback_source': submission.feedback_source,
            'created_at': submission.created_at,
        }
        for submission in session.user.submissions.select_related('exercise').all()
    ]


@submission_router.get('/{submission_id}', response={200: SubmissionSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Retorna a submissão atualizada para polling do feedback.')
def get_submission(request, submission_id: int, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    submission = Submission.objects.select_related('exercise').filter(id=submission_id, user=session.user).first()
    if submission is None:
        return 404, {'message': 'Submissão não encontrada.'}

    return 200, serialize_submission(submission)


@submission_router.post('/{submission_id}/review-chat', response={200: ReviewChatResponseSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Continua a revisão com IA sobre uma submissão específica.')
def review_chat(request, submission_id: int, payload: ReviewChatInputSchema, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    submission = Submission.objects.select_related('exercise').filter(id=submission_id, user=session.user).first()
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


api.add_router('/auth', auth_router)
api.add_router('/exercises', exercise_router)
api.add_router('/submissions', submission_router)
api.add_router('', system_router)
