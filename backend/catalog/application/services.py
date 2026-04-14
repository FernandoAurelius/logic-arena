from arena.models import (
    Exercise,
    ExerciseCategory,
    ExerciseTestCase,
    ExerciseTrack,
    ExerciseType,
    LearningModule,
)
from arena.services import sync_exercise_explanation
from progress.application.services import build_module_progress_summary, build_track_progress_summary


DEFAULT_EXERCISE_TYPE_SLUG = 'drill-de-implementacao'
DEFAULT_EXERCISE_TYPE_LABEL = 'Drill de implementação'


def build_exercise_catalog_meta(exercise: Exercise) -> dict:
    exercise_type = exercise.exercise_type.slug if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_SLUG
    return {
        'exercise_type': exercise_type,
        'exercise_type_label': exercise.exercise_type.name if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_LABEL,
        'estimated_time_minutes': exercise.estimated_time_minutes or 15,
        'concept_summary': exercise.concept_summary or exercise.professor_note,
        'pedagogical_brief': exercise.pedagogical_brief or exercise.professor_note,
        'track_position': exercise.track_position or 0,
    }

def serialize_exercise_summary(exercise: Exercise) -> dict:
    meta = build_exercise_catalog_meta(exercise)
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
        'exercise_type': meta['exercise_type'],
        'exercise_type_label': meta['exercise_type_label'],
        'estimated_time_minutes': meta['estimated_time_minutes'],
        'concept_summary': meta['concept_summary'],
        'track_position': meta['track_position'],
        'module_slug': exercise.track.module.slug if exercise.track and exercise.track.module else None,
        'module_name': exercise.track.module.name if exercise.track and exercise.track.module else None,
        'category_slug': exercise.category.slug if exercise.category else None,
        'category_name': exercise.category.name if exercise.category else None,
        'track_slug': exercise.track.slug if exercise.track else None,
        'track_name': exercise.track.name if exercise.track else None,
    }


def create_exercise(payload) -> Exercise:
    category = None
    track = None
    module = None
    exercise_type = None
    if payload.category_slug and payload.category_name:
        category, _ = ExerciseCategory.objects.get_or_create(
            slug=payload.category_slug,
            defaults={'name': payload.category_name},
        )
    if payload.module_slug and payload.module_name:
        module, _ = LearningModule.objects.get_or_create(
            slug=payload.module_slug,
            defaults={
                'name': payload.module_name,
                'description': payload.module_description,
                'audience': payload.module_audience,
                'source_kind': payload.module_source_kind,
                'status': LearningModule.STATUS_ACTIVE,
            },
        )
    if payload.track_slug and payload.track_name and category is not None:
        track, _ = ExerciseTrack.objects.get_or_create(
            slug=payload.track_slug,
            defaults={
                'name': payload.track_name,
                'category': category,
                'module': module,
            },
        )
    elif payload.track_slug:
        track = ExerciseTrack.objects.filter(slug=payload.track_slug).first()

    if payload.exercise_type_slug:
        exercise_type = ExerciseType.objects.filter(slug=payload.exercise_type_slug).first()
    if exercise_type is None:
        exercise_type = ExerciseType.objects.filter(slug=DEFAULT_EXERCISE_TYPE_SLUG).first()

    exercise = Exercise.objects.create(
        slug=payload.slug,
        title=payload.title,
        statement=payload.statement,
        difficulty=payload.difficulty,
        language=payload.language,
        category=category or (track.category if track else None),
        track=track,
        exercise_type=exercise_type,
        estimated_time_minutes=payload.estimated_time_minutes,
        track_position=payload.track_position,
        concept_summary=payload.concept_summary,
        pedagogical_brief=payload.pedagogical_brief,
        starter_code=payload.starter_code,
        sample_input=payload.sample_input,
        sample_output=payload.sample_output,
        professor_note=payload.professor_note,
    )
    ExerciseTestCase.objects.bulk_create(
        [
            ExerciseTestCase(
                exercise=exercise,
                input_data=test_case.input_data,
                expected_output=test_case.expected_output,
                is_hidden=test_case.is_hidden,
            )
            for test_case in payload.test_cases
        ]
    )
    sync_exercise_explanation(exercise)
    return exercise
