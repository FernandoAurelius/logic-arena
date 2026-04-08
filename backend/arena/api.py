from django.shortcuts import get_object_or_404
from ninja import Header, NinjaAPI, Router

from .models import AuthSession, Exercise
from .schemas import (
    ErrorSchema,
    ExerciseCreateSchema,
    ExerciseDetailSchema,
    ExerciseSummarySchema,
    LoginInputSchema,
    LoginResponseSchema,
    SubmissionInputSchema,
    SubmissionSchema,
    SubmissionSummarySchema,
    UserSchema,
)
from .services import create_exercise, evaluate_submission, get_or_create_session


api = NinjaAPI(
    title='Logic Arena API',
    version='0.1.0',
    description='API do MVP do Logic Arena com autenticação simples, exercícios persistidos e submissões avaliadas.',
    urls_namespace='logic_arena_api',
)

auth_router = Router(tags=['auth'])
exercise_router = Router(tags=['exercises'])
submission_router = Router(tags=['submissions'])


def require_session(authorization: str | None) -> AuthSession:
    if not authorization or not authorization.startswith('Bearer '):
        raise PermissionError('Token ausente ou inválido.')
    token = authorization.replace('Bearer ', '', 1).strip()
    session = AuthSession.objects.select_related('user').filter(token=token).first()
    if session is None:
        raise PermissionError('Sessão não encontrada.')
    return session


@auth_router.post('/login', response={200: LoginResponseSchema, 401: ErrorSchema}, summary='Faz login ou cria o usuário automaticamente.')
def login(request, payload: LoginInputSchema):
    try:
        session, created = get_or_create_session(payload.nickname.strip(), payload.password)
    except ValueError as error:
        return 401, {'message': str(error)}

    return 200, {
        'token': session.token,
        'created': created,
        'user': {
            'id': session.user.id,
            'nickname': session.user.nickname,
            'created_at': session.user.created_at,
        },
    }


@auth_router.get('/me', response={200: UserSchema, 401: ErrorSchema}, summary='Retorna o usuário autenticado.')
def me(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    return 200, session.user


@exercise_router.get('/', response=list[ExerciseSummarySchema], summary='Lista exercícios ativos.')
def list_exercises(request):
    return Exercise.objects.filter(is_active=True)


@exercise_router.get('/{slug}', response=ExerciseDetailSchema, summary='Detalha um exercício específico.')
def get_exercise(request, slug: str):
    exercise = get_object_or_404(Exercise.objects.prefetch_related('test_cases'), slug=slug, is_active=True)
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
        'statement': exercise.statement,
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'test_cases': list(exercise.test_cases.filter(is_hidden=False)),
    }


@exercise_router.post('/', response={201: ExerciseDetailSchema, 400: ErrorSchema}, summary='Cadastra um exercício novo via API.')
def post_exercise(request, payload: ExerciseCreateSchema):
    if Exercise.objects.filter(slug=payload.slug).exists():
        return 400, {'message': 'Já existe um exercício com esse slug.'}

    exercise = create_exercise(payload)
    return 201, {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
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
    return 200, {
        'id': submission.id,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'console_output': submission.console_output,
        'feedback': submission.feedback,
        'created_at': submission.created_at,
        'results': results,
    }


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
            'created_at': submission.created_at,
        }
        for submission in session.user.submissions.select_related('exercise').all()
    ]


api.add_router('/auth', auth_router)
api.add_router('/exercises', exercise_router)
api.add_router('/submissions', submission_router)
