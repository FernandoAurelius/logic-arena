from __future__ import annotations

from django.db.models import Prefetch

from .models import Exercise, ExerciseTrack, LearningModule, Submission


def list_active_exercises():
    return Exercise.objects.filter(is_active=True).select_related('category', 'track', 'track__module', 'exercise_type')


def get_active_exercise_by_slug(slug: str):
    return list_active_exercises().prefetch_related('test_cases').filter(slug=slug).first()


def list_navigator_modules():
    track_queryset = ExerciseTrack.objects.select_related('category', 'module').prefetch_related('exercises')
    return LearningModule.objects.prefetch_related(Prefetch('tracks', queryset=track_queryset)).all()


def get_module_by_slug(module_slug: str):
    track_queryset = ExerciseTrack.objects.select_related('category', 'module').prefetch_related('exercises')
    return LearningModule.objects.prefetch_related(Prefetch('tracks', queryset=track_queryset)).filter(slug=module_slug).first()


def get_track_by_slug(track_slug: str):
    return (
        ExerciseTrack.objects.select_related('category', 'module')
        .prefetch_related('concepts', 'prerequisites')
        .filter(slug=track_slug)
        .first()
    )


def get_exercise_for_track(track: ExerciseTrack, exercise_slug: str):
    return Exercise.objects.select_related('track').filter(slug=exercise_slug, track=track, is_active=True).first()


def get_submission_for_user(user, submission_id: int):
    return Submission.objects.select_related('exercise').filter(id=submission_id, user=user).first()


def list_user_submissions(user):
    return user.submissions.select_related('exercise').all()
