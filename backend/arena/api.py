from django.shortcuts import get_object_or_404
from ninja import Header, NinjaAPI, Router

from .models import AuthSession, Exercise, ExerciseCategory, ExerciseTrack, ExerciseType, LearningModule, Submission, UserExerciseProgress
from .schemas import (
    CatalogAdminReferenceSchema,
    ExerciseExplanationSchema,
    ErrorSchema,
    ExerciseCreateSchema,
    ExerciseCatalogUpdateSchema,
    ExerciseDetailSchema,
    ExerciseSummarySchema,
    ExerciseTypeInputSchema,
    LearningModuleInputSchema,
    LoginInputSchema,
    LoginResponseSchema,
    ModuleDetailSchema,
    NavigatorResponseSchema,
    ReviewChatInputSchema,
    ReviewChatResponseSchema,
    SubmissionInputSchema,
    SubmissionSchema,
    SubmissionSummarySchema,
    TrackInputSchema,
    TrackDetailSchema,
    TrackUpdateSchema,
    UserSchema,
)
from .feedback import review_submission_chat
from .services import (
    build_exercise_progress_payload,
    build_exercise_catalog_meta,
    build_module_progress_summary,
    build_track_progress_summary,
    build_user_progress_summary,
    build_user_schema_payload,
    create_exercise,
    ensure_exercise_explanation,
    evaluate_submission,
    get_or_create_session,
    resolve_evaluation_plan,
    resolve_exercise_family_key,
    resolve_workspace_spec,
    sync_exercise_explanation,
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
catalog_router = Router(tags=['catalog'])
catalog_admin_router = Router(tags=['catalog-admin'])
system_router = Router(tags=['system'])


def require_session(authorization: str | None) -> AuthSession:
    if not authorization or not authorization.startswith('Bearer '):
        raise PermissionError('Token ausente ou inválido.')
    token = authorization.replace('Bearer ', '', 1).strip()
    session = AuthSession.objects.select_related('user').filter(token=token).first()
    if session is None:
        raise PermissionError('Sessão não encontrada.')
    return session


def require_catalog_admin(authorization: str | None) -> AuthSession:
    session = require_session(authorization)
    if not session.user.is_catalog_admin:
        raise PermissionError('Usuário não possui permissão para administrar o catálogo.')
    return session


def serialize_submission(submission: Submission) -> dict:
    progress = UserExerciseProgress.objects.filter(user=submission.user, exercise=submission.exercise).first()
    return {
        'id': submission.id,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'source_code': submission.source_code,
        'submission_payload': submission.submission_payload,
        'evidence_bundle': submission.evidence_bundle,
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
    meta = build_exercise_catalog_meta(exercise)
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'family_key': meta['family_key'],
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
        'exercise_type': meta['exercise_type'],
        'exercise_type_label': meta['exercise_type_label'],
        'estimated_time_minutes': meta['estimated_time_minutes'],
        'concept_summary': meta['concept_summary'],
        'track_position': meta['track_position'],
        'surface_key': meta['surface_key'],
        'workspace_kind': meta['workspace_kind'],
        'module_slug': exercise.track.module.slug if exercise.track and exercise.track.module else None,
        'module_name': exercise.track.module.name if exercise.track and exercise.track.module else None,
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
    exercises = Exercise.objects.filter(is_active=True).select_related('category', 'track', 'track__module', 'exercise_type')
    return 200, [serialize_exercise_summary(exercise) for exercise in exercises]


@exercise_router.get('/{slug}', response={200: ExerciseDetailSchema, 401: ErrorSchema}, summary='Detalha um exercício específico.')
def get_exercise(request, slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    exercise = get_object_or_404(Exercise.objects.prefetch_related('test_cases').select_related('category', 'track', 'track__module', 'exercise_type'), slug=slug, is_active=True)
    return 200, {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'content_blocks': exercise.content_blocks,
        'workspace_spec': resolve_workspace_spec(exercise),
        'evaluation_plan': resolve_evaluation_plan(exercise),
        'review_profile': exercise.review_profile,
        'test_cases': list(exercise.test_cases.filter(is_hidden=False)),
    }


@catalog_router.get('/navigator', response={200: NavigatorResponseSchema, 401: ErrorSchema}, summary='Retorna a visão autenticada do catálogo por módulo e trilha.')
def get_navigator(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    modules = LearningModule.objects.prefetch_related('tracks__exercises').all()
    serialized_modules = []
    recommended_module_slug = None
    recommended_module_name = None
    recommended_track_slug = None
    recommended_track_name = None

    for module in modules:
        serialized_tracks = []
        for track in module.tracks.all():
            summary = build_track_progress_summary(track, session.user)
            current_target = summary['current_target']
            if recommended_track_slug is None and current_target is not None:
                recommended_module_slug = module.slug
                recommended_module_name = module.name
                recommended_track_slug = track.slug
                recommended_track_name = track.name
            serialized_tracks.append(
                {
                    'slug': track.slug,
                    'name': track.name,
                    'module_slug': module.slug,
                    'module_name': module.name,
                    'category_slug': track.category.slug,
                    'category_name': track.category.name,
                    'description': track.description,
                    'goal': track.goal or track.description,
                    'level_label': track.level_label or 'Trilha ativa',
                    'progress_percent': summary['progress_percent'],
                    'completed_exercises': summary['completed'],
                    'total_exercises': summary['total'],
                    'current_target_slug': current_target.slug if current_target else None,
                    'current_target_title': current_target.title if current_target else None,
                }
            )
        serialized_modules.append(
            {
                'slug': module.slug,
                'name': module.name,
                'description': module.description,
                'audience': module.audience,
                'source_kind': module.source_kind,
                'status': module.status,
                'tracks': serialized_tracks,
            }
        )

    return 200, {
        'recommended_module_slug': recommended_module_slug,
        'recommended_module_name': recommended_module_name,
        'recommended_track_slug': recommended_track_slug,
        'recommended_track_name': recommended_track_name,
        'modules': serialized_modules,
    }


@catalog_router.get('/modules/{module_slug}', response={200: ModuleDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Retorna o detalhe de um módulo com suas trilhas.')
def get_module_detail(request, module_slug: str, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    module = LearningModule.objects.prefetch_related('tracks__exercises').filter(slug=module_slug).first()
    if module is None:
        return 404, {'message': 'Módulo não encontrado.'}

    summary = build_module_progress_summary(module, session.user)

    return 200, {
        'slug': module.slug,
        'name': module.name,
        'description': module.description,
        'audience': module.audience,
        'source_kind': module.source_kind,
        'status': module.status,
        'progress_percent': summary['progress_percent'],
        'completed_tracks': summary['completed_tracks'],
        'total_tracks': summary['total_tracks'],
        'current_target_track_slug': summary['current_target_track'].slug if summary['current_target_track'] else None,
        'current_target_track_name': summary['current_target_track'].name if summary['current_target_track'] else None,
        'current_target_exercise_slug': summary['current_target_exercise'].slug if summary['current_target_exercise'] else None,
        'current_target_exercise_title': summary['current_target_exercise'].title if summary['current_target_exercise'] else None,
        'tracks': [
            {
                'slug': track_summary['track'].slug,
                'name': track_summary['track'].name,
                'module_slug': module.slug,
                'module_name': module.name,
                'category_slug': track_summary['track'].category.slug,
                'category_name': track_summary['track'].category.name,
                'description': track_summary['track'].description,
                'goal': track_summary['track'].goal or track_summary['track'].description,
                'level_label': track_summary['track'].level_label or 'Trilha ativa',
                'progress_percent': track_summary['progress_percent'],
                'completed_exercises': track_summary['completed'],
                'total_exercises': track_summary['total'],
                'current_target_slug': track_summary['current_target'].slug if track_summary['current_target'] else None,
                'current_target_title': track_summary['current_target'].title if track_summary['current_target'] else None,
            }
            for track_summary in summary['tracks']
        ],
    }


@catalog_router.get('/tracks/{track_slug}', response={200: TrackDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Retorna a página de trilha com progresso, conceitos e exercícios.')
def get_track_detail(request, track_slug: str, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    track = ExerciseTrack.objects.select_related('category', 'module').prefetch_related('concepts', 'prerequisites').filter(slug=track_slug).first()
    if track is None:
        return 404, {'message': 'Trilha não encontrada.'}

    summary = build_track_progress_summary(track, session.user)
    current_target = summary['current_target']
    exercises = []
    first_unfinished_seen = False

    for index, exercise in enumerate(summary['exercises'], start=1):
        progress = summary['progress_index'].get(exercise.id)
        meta = build_exercise_catalog_meta(exercise)
        passed_once = bool(progress and 'passed_once' in (progress.awarded_progress_markers or []))
        attempts_count = progress.attempts_count if progress else 0

        if passed_once:
            status = 'passed'
        elif not first_unfinished_seen:
            status = 'in_progress' if attempts_count > 0 else 'available'
            first_unfinished_seen = True
        else:
            status = 'locked'

        exercises.append(
            {
                **serialize_exercise_summary(exercise),
                'position': index,
                'pedagogical_brief': meta['pedagogical_brief'],
                'is_current_target': current_target is not None and exercise.slug == current_target.slug,
                'progress': {
                    'status': status,
                    'attempts_count': attempts_count,
                    'best_passed_tests': progress.best_passed_tests if progress else 0,
                    'best_total_tests': progress.best_total_tests if progress else 0,
                    'passed_once': passed_once,
                },
            }
        )

    remaining_exercises = max(0, summary['total'] - summary['completed'])
    milestone_unlocked = remaining_exercises <= 1 and summary['total'] > 0

    return 200, {
        'slug': track.slug,
        'name': track.name,
        'module_slug': track.module.slug if track.module else None,
        'module_name': track.module.name if track.module else None,
        'category_slug': track.category.slug,
        'category_name': track.category.name,
        'description': track.description,
        'goal': track.goal or track.description,
        'level_label': track.level_label or 'Trilha ativa',
        'progress_percent': summary['progress_percent'],
        'completed_exercises': summary['completed'],
        'total_exercises': summary['total'],
        'current_target_slug': current_target.slug if current_target else None,
        'current_target_title': current_target.title if current_target else None,
        'concept_kicker': track.concept_kicker or 'Conceitos trabalhados',
        'concepts': [
            {
                'title': concept.title,
                'summary': concept.summary,
                'why_it_matters': concept.why_it_matters,
                'common_mistake': concept.common_mistake,
            }
            for concept in track.concepts.all()
        ],
        'prerequisites': [prerequisite.label for prerequisite in track.prerequisites.all()],
        'exercises': exercises,
        'milestone': {
            'title': track.milestone_title or 'Checkpoint da trilha',
            'summary': track.milestone_summary or 'Marco especial de consolidação desta trilha.',
            'requirement_label': track.milestone_requirement_label or 'Concluir os módulos principais da trilha.',
            'unlocked': milestone_unlocked,
            'remaining_exercises': remaining_exercises,
        },
    }


@catalog_router.get(
    '/tracks/{track_slug}/explanations/{exercise_slug}',
    response={200: ExerciseExplanationSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna a documentação técnica progressiva de um módulo específico da trilha.',
)
def get_track_explanation(request, track_slug: str, exercise_slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    track = ExerciseTrack.objects.select_related('category', 'module').prefetch_related('concepts', 'prerequisites').filter(slug=track_slug).first()
    if track is None:
        return 404, {'message': 'Trilha não encontrada.'}

    exercise = Exercise.objects.select_related('track').filter(slug=exercise_slug, track=track, is_active=True).first()
    if exercise is None:
        return 404, {'message': 'Módulo não encontrado para essa trilha.'}

    explanation = ensure_exercise_explanation(exercise)
    explanation = type(explanation).objects.prefetch_related('concepts', 'code_examples').get(pk=explanation.pk)
    meta = build_exercise_catalog_meta(exercise)

    return 200, {
        'module_slug': track.module.slug if track.module else None,
        'module_name': track.module.name if track.module else None,
        'track_slug': track.slug,
        'track_name': track.name,
        'track_goal': track.goal or track.description,
        'level_label': track.level_label or 'Trilha ativa',
        'exercise_slug': exercise.slug,
        'exercise_title': exercise.title,
        'exercise_type_label': meta['exercise_type_label'],
        'estimated_time_minutes': meta['estimated_time_minutes'],
        'concept_summary': meta['concept_summary'],
        'pedagogical_brief': meta['pedagogical_brief'],
        'learning_goal': explanation.learning_goal,
        'concept_focus_markdown': explanation.concept_focus_markdown,
        'reading_strategy_markdown': explanation.reading_strategy_markdown,
        'implementation_strategy_markdown': explanation.implementation_strategy_markdown,
        'assessment_notes_markdown': explanation.assessment_notes_markdown,
        'common_mistakes': list(explanation.common_mistakes or []),
        'mastery_checklist': list(explanation.mastery_checklist or []),
        'prerequisites': [prerequisite.label for prerequisite in track.prerequisites.all()],
        'concepts': [
            {
                'title': concept.title,
                'explanation_text': concept.explanation_text,
                'why_it_matters': concept.why_it_matters,
                'common_mistake': concept.common_mistake,
            }
            for concept in explanation.concepts.all()
        ],
        'code_examples': [
            {
                'title': example.title,
                'rationale': example.rationale,
                'language': example.language,
                'code': example.code,
            }
            for example in explanation.code_examples.all()
        ],
    }


@catalog_admin_router.get('/reference', response={200: CatalogAdminReferenceSchema, 401: ErrorSchema}, summary='Retorna as referências básicas para administração do catálogo.')
def get_catalog_reference(request, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    return 200, {
        'modules': [
            {
                'slug': module.slug,
                'name': module.name,
                'description': module.description,
                'audience': module.audience,
                'source_kind': module.source_kind,
                'status': module.status,
                'sort_order': module.sort_order,
            }
            for module in LearningModule.objects.all()
        ],
        'exercise_types': [
            {
                'slug': exercise_type.slug,
                'name': exercise_type.name,
                'description': exercise_type.description,
                'sort_order': exercise_type.sort_order,
            }
            for exercise_type in ExerciseType.objects.all()
        ],
        'categories': [
            {
                'slug': category.slug,
                'name': category.name,
                'description': category.description,
                'sort_order': category.sort_order,
            }
            for category in ExerciseCategory.objects.all()
        ],
        'tracks': [
            {
                'slug': track.slug,
                'name': track.name,
                'module_slug': track.module.slug if track.module else None,
                'category_slug': track.category.slug,
                'sort_order': track.sort_order,
            }
            for track in ExerciseTrack.objects.select_related('module', 'category').all()
        ],
    }


@catalog_admin_router.get('/modules', response={200: list[LearningModuleInputSchema], 401: ErrorSchema}, summary='Lista módulos administráveis.')
def list_modules(request, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    return 200, [
        {
            'slug': module.slug,
            'name': module.name,
            'description': module.description,
            'audience': module.audience,
            'source_kind': module.source_kind,
            'status': module.status,
            'sort_order': module.sort_order,
        }
        for module in LearningModule.objects.all()
    ]


@catalog_admin_router.post('/modules', response={200: LearningModuleInputSchema, 401: ErrorSchema}, summary='Cria ou atualiza um módulo.')
def upsert_module(request, payload: LearningModuleInputSchema, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    module, _ = LearningModule.objects.update_or_create(
        slug=payload.slug,
        defaults={
            'name': payload.name,
            'description': payload.description,
            'audience': payload.audience,
            'source_kind': payload.source_kind,
            'status': payload.status,
            'sort_order': payload.sort_order,
        },
    )
    return 200, {
        'slug': module.slug,
        'name': module.name,
        'description': module.description,
        'audience': module.audience,
        'source_kind': module.source_kind,
        'status': module.status,
        'sort_order': module.sort_order,
    }


@catalog_admin_router.get('/exercise-types', response={200: list[ExerciseTypeInputSchema], 401: ErrorSchema}, summary='Lista tipos de exercício administráveis.')
def list_exercise_types(request, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    return 200, [
        {
            'slug': exercise_type.slug,
            'name': exercise_type.name,
            'description': exercise_type.description,
            'sort_order': exercise_type.sort_order,
        }
        for exercise_type in ExerciseType.objects.all()
    ]


@catalog_admin_router.post('/exercise-types', response={200: ExerciseTypeInputSchema, 401: ErrorSchema}, summary='Cria ou atualiza um tipo de exercício.')
def upsert_exercise_type(request, payload: ExerciseTypeInputSchema, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    exercise_type, _ = ExerciseType.objects.update_or_create(
        slug=payload.slug,
        defaults={
            'name': payload.name,
            'description': payload.description,
            'sort_order': payload.sort_order,
        },
    )
    return 200, {
        'slug': exercise_type.slug,
        'name': exercise_type.name,
        'description': exercise_type.description,
        'sort_order': exercise_type.sort_order,
    }


@catalog_admin_router.get('/tracks', response={200: list[TrackDetailSchema], 401: ErrorSchema}, summary='Lista trilhas administráveis.')
def list_tracks(request, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    tracks = ExerciseTrack.objects.select_related('category', 'module').prefetch_related('concepts', 'prerequisites').all()
    return 200, [
        {
            'slug': track.slug,
            'name': track.name,
            'module_slug': track.module.slug if track.module else None,
            'module_name': track.module.name if track.module else None,
            'category_slug': track.category.slug,
            'category_name': track.category.name,
            'description': track.description,
            'goal': track.goal or track.description,
            'level_label': track.level_label or 'Trilha ativa',
            'progress_percent': 0,
            'completed_exercises': 0,
            'total_exercises': track.exercises.filter(is_active=True).count(),
            'current_target_slug': None,
            'current_target_title': None,
            'concept_kicker': track.concept_kicker or 'Conceitos trabalhados',
            'concepts': [
                {
                    'title': concept.title,
                    'summary': concept.summary,
                    'why_it_matters': concept.why_it_matters,
                    'common_mistake': concept.common_mistake,
                }
                for concept in track.concepts.all()
            ],
            'prerequisites': [prerequisite.label for prerequisite in track.prerequisites.all()],
            'exercises': [],
            'milestone': {
                'title': track.milestone_title or 'Checkpoint da trilha',
                'summary': track.milestone_summary or 'Marco especial de consolidação desta trilha.',
                'requirement_label': track.milestone_requirement_label or 'Concluir os módulos principais da trilha.',
                'unlocked': False,
                'remaining_exercises': track.exercises.filter(is_active=True).count(),
            },
        }
        for track in tracks
    ]


@catalog_admin_router.post('/tracks', response={200: TrackDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Cria uma trilha e seus metadados editoriais.')
def create_track(request, payload: TrackInputSchema, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    module = LearningModule.objects.filter(slug=payload.module_slug).first()
    category = ExerciseCategory.objects.filter(slug=payload.category_slug).first()
    if module is None or category is None:
        return 404, {'message': 'Módulo ou categoria não encontrados.'}

    track = ExerciseTrack.objects.create(
        slug=payload.slug,
        name=payload.name,
        module=module,
        category=category,
        description=payload.description,
        goal=payload.goal,
        level_label=payload.level_label,
        concept_kicker=payload.concept_kicker,
        milestone_title=payload.milestone_title,
        milestone_summary=payload.milestone_summary,
        milestone_requirement_label=payload.milestone_requirement_label,
        sort_order=payload.sort_order,
    )

    track.concepts.bulk_create([
        track.concepts.model(
            track=track,
            title=concept.title,
            summary=concept.summary,
            why_it_matters=concept.why_it_matters,
            common_mistake=concept.common_mistake,
            sort_order=concept.sort_order,
        )
        for concept in payload.concepts
    ])
    track.prerequisites.bulk_create([
        track.prerequisites.model(
            track=track,
            label=prerequisite.label,
            sort_order=prerequisite.sort_order,
        )
        for prerequisite in payload.prerequisites
    ])

    return get_track_detail(request, track.slug, authorization)


@catalog_admin_router.patch('/tracks/{track_slug}', response={200: TrackDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Atualiza metadados de uma trilha.')
def update_track(request, track_slug: str, payload: TrackUpdateSchema, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    track = ExerciseTrack.objects.select_related('category', 'module').prefetch_related('concepts', 'prerequisites').filter(slug=track_slug).first()
    if track is None:
        return 404, {'message': 'Trilha não encontrada.'}

    if payload.module_slug is not None:
        track.module = LearningModule.objects.filter(slug=payload.module_slug).first()
    if payload.category_slug is not None:
        category = ExerciseCategory.objects.filter(slug=payload.category_slug).first()
        if category is None:
            return 404, {'message': 'Categoria não encontrada.'}
        track.category = category

    for field in ['name', 'description', 'goal', 'level_label', 'concept_kicker', 'milestone_title', 'milestone_summary', 'milestone_requirement_label', 'sort_order']:
        value = getattr(payload, field)
        if value is not None:
            setattr(track, field, value)
    track.save()

    if payload.concepts is not None:
        track.concepts.all().delete()
        track.concepts.bulk_create([
            track.concepts.model(
                track=track,
                title=concept.title,
                summary=concept.summary,
                why_it_matters=concept.why_it_matters,
                common_mistake=concept.common_mistake,
                sort_order=concept.sort_order,
            )
            for concept in payload.concepts
        ])

    if payload.prerequisites is not None:
        track.prerequisites.all().delete()
        track.prerequisites.bulk_create([
            track.prerequisites.model(
                track=track,
                label=prerequisite.label,
                sort_order=prerequisite.sort_order,
            )
            for prerequisite in payload.prerequisites
        ])

    return get_track_detail(request, track.slug, authorization)


@catalog_admin_router.patch('/exercises/{slug}/catalog', response={200: ExerciseDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Atualiza metadados catalogais de um exercício.')
def update_exercise_catalog(request, slug: str, payload: ExerciseCatalogUpdateSchema, authorization: str | None = Header(default=None)):
    try:
        require_catalog_admin(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    exercise = Exercise.objects.select_related('track', 'category').prefetch_related('test_cases').filter(slug=slug).first()
    if exercise is None:
        return 404, {'message': 'Exercício não encontrado.'}

    if payload.track_slug is not None:
        track = ExerciseTrack.objects.select_related('category').filter(slug=payload.track_slug).first()
        if track is None:
            return 404, {'message': 'Trilha não encontrada.'}
        exercise.track = track
        exercise.category = track.category
    if payload.exercise_type_slug is not None:
        exercise_type = ExerciseType.objects.filter(slug=payload.exercise_type_slug).first()
        if exercise_type is None:
            return 404, {'message': 'Tipo de exercício não encontrado.'}
        exercise.exercise_type = exercise_type

    for field in ['estimated_time_minutes', 'track_position', 'concept_summary', 'pedagogical_brief']:
        value = getattr(payload, field)
        if value is not None:
            setattr(exercise, field, value)
    exercise.save()
    sync_exercise_explanation(exercise)

    return 200, {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'test_cases': list(exercise.test_cases.all()),
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
        'content_blocks': exercise.content_blocks,
        'workspace_spec': resolve_workspace_spec(exercise),
        'evaluation_plan': resolve_evaluation_plan(exercise),
        'review_profile': exercise.review_profile,
        'test_cases': list(exercise.test_cases.all()),
    }


@submission_router.post('/exercises/{slug}/submit', response={200: SubmissionSchema, 401: ErrorSchema}, summary='Executa os testes, persiste a submissão e devolve o resultado.')
def submit_exercise(request, slug: str, payload: SubmissionInputSchema, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    exercise = get_object_or_404(Exercise.objects.prefetch_related('test_cases'), slug=slug, is_active=True)
    submission, results = evaluate_submission(session.user, exercise, payload)
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
        context={
            'family_key': resolve_exercise_family_key(submission.exercise),
            'workspace_spec': resolve_workspace_spec(submission.exercise),
            'evaluation_plan': resolve_evaluation_plan(submission.exercise),
            'submission_payload': submission.submission_payload,
            'evidence_bundle': submission.evidence_bundle,
        },
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
api.add_router('/catalog', catalog_router)
api.add_router('/catalog-admin', catalog_admin_router)
api.add_router('', system_router)
