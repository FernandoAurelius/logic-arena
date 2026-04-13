from arena.explanation_builder import build_explanation_blueprint
from arena.models import Exercise
from arena.services import ensure_exercise_explanation as _ensure_exercise_explanation
from arena.services import sync_exercise_explanation as _sync_exercise_explanation
from progress.application.services import build_module_progress_summary, build_track_progress_summary


def ensure_exercise_explanation(exercise: Exercise):
    return _ensure_exercise_explanation(exercise)


def sync_exercise_explanation(exercise: Exercise):
    return _sync_exercise_explanation(exercise)


def build_explanation_blueprint_for_exercise(exercise: Exercise):
    return build_explanation_blueprint(exercise)
