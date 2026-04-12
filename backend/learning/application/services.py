from arena.explanation_builder import build_explanation_blueprint
from arena.models import Exercise, ExerciseTrack, LearningModule, UserExerciseProgress
from arena.services import ensure_exercise_explanation as _ensure_exercise_explanation
from arena.services import sync_exercise_explanation as _sync_exercise_explanation


def build_track_progress_index(user, exercises: list[Exercise]) -> dict[int, UserExerciseProgress]:
    progress_entries = UserExerciseProgress.objects.filter(
        user=user,
        exercise__in=exercises,
    ).select_related('exercise')
    return {entry.exercise_id: entry for entry in progress_entries}


def build_track_progress_summary(track: ExerciseTrack, user) -> dict:
    exercises = list(track.exercises.filter(is_active=True).select_related('category', 'track', 'exercise_type', 'track__module'))
    exercises.sort(key=lambda exercise: ((exercise.track_position or 9999), exercise.title))
    progress_index = build_track_progress_index(user, exercises)
    completed = 0
    current_target = None

    for exercise in exercises:
        progress = progress_index.get(exercise.id)
        passed_once = bool(progress and 'passed_once' in (progress.awarded_progress_markers or []))
        if passed_once:
            completed += 1
            continue
        if current_target is None:
            current_target = exercise

    progress_percent = round((completed / len(exercises)) * 100) if exercises else 0

    return {
        'track': track,
        'exercises': exercises,
        'progress_index': progress_index,
        'completed': completed,
        'total': len(exercises),
        'progress_percent': progress_percent,
        'current_target': current_target,
    }


def build_module_progress_summary(module: LearningModule, user) -> dict:
    tracks = list(module.tracks.select_related('category', 'module').all())
    track_summaries = [build_track_progress_summary(track, user) for track in tracks]
    completed_tracks = sum(1 for summary in track_summaries if summary['total'] > 0 and summary['completed'] == summary['total'])
    current_target_track = next((summary['track'] for summary in track_summaries if summary['current_target'] is not None), None)
    current_target_exercise = next((summary['current_target'] for summary in track_summaries if summary['current_target'] is not None), None)
    progress_percent = round((completed_tracks / len(tracks)) * 100) if tracks else 0
    return {
        'module': module,
        'tracks': track_summaries,
        'completed_tracks': completed_tracks,
        'total_tracks': len(tracks),
        'progress_percent': progress_percent,
        'current_target_track': current_target_track,
        'current_target_exercise': current_target_exercise,
    }


def ensure_exercise_explanation(exercise: Exercise):
    return _ensure_exercise_explanation(exercise)


def sync_exercise_explanation(exercise: Exercise):
    return _sync_exercise_explanation(exercise)


def build_explanation_blueprint_for_exercise(exercise: Exercise):
    return build_explanation_blueprint(exercise)
