from dataclasses import asdict

from django.db import transaction
from django.utils import timezone

from apps.arena.models import ArenaUser, Exercise, ExerciseTrack, LearningModule, Submission, UserExerciseProgress
from apps.progress.selectors import list_user_progress_for_exercises
from apps.progress.domain import (
    PASSED_ONCE_MARKER,
    PASSED_ONCE_XP,
    ProgressReward,
    ProgressStateSnapshot,
    SubmissionSnapshot,
    build_exercise_progress_payload,
    build_user_progress_summary_from_xp,
    compute_submission_progress_update,
)


class ProgressRewardFactoryProtocol:
    def __call__(self, milestone_key: str, label: str, xp_awarded: int): ...


def build_user_progress_summary(user: ArenaUser) -> dict:
    return build_user_progress_summary_from_xp(user.xp_total)


def build_track_progress_index(user: ArenaUser, exercises: list[Exercise]) -> dict[int, UserExerciseProgress]:
    progress_entries = list_user_progress_for_exercises(user, exercises)
    return {entry.exercise_id: entry for entry in progress_entries}


def build_track_progress_summary(track: ExerciseTrack, user: ArenaUser) -> dict:
    exercises = list(track.exercises.filter(is_active=True).select_related('category', 'track', 'exercise_type', 'track__module'))
    exercises.sort(key=lambda exercise: ((exercise.track_position or 9999), exercise.title))
    progress_index = build_track_progress_index(user, exercises)
    completed = 0
    current_target = None

    for exercise in exercises:
        progress = progress_index.get(exercise.id)
        passed_once = bool(progress and PASSED_ONCE_MARKER in (progress.awarded_progress_markers or []))
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


def build_module_progress_summary(module: LearningModule, user: ArenaUser) -> dict:
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


def apply_submission_progress(
    user: ArenaUser,
    exercise: Exercise,
    submission: Submission,
    reward_factory: ProgressRewardFactoryProtocol | None = None,
) -> tuple[UserExerciseProgress, list, int]:
    reward_factory = reward_factory or ProgressReward
    with transaction.atomic():
        locked_user = ArenaUser.objects.select_for_update().get(pk=user.pk)
        progress, _ = UserExerciseProgress.objects.select_for_update().get_or_create(
            user=locked_user,
            exercise=exercise,
        )

        progress.last_submission = submission
        update = compute_submission_progress_update(
            ProgressStateSnapshot(
                attempts_count=progress.attempts_count,
                best_passed_tests=progress.best_passed_tests,
                best_total_tests=progress.best_total_tests,
                best_ratio=progress.best_ratio or 0,
                xp_awarded_total=progress.xp_awarded_total,
                awarded_progress_markers=tuple(progress.awarded_progress_markers or []),
            ),
            SubmissionSnapshot(
                status=submission.status,
                passed_tests=submission.passed_tests,
                total_tests=submission.total_tests,
            ),
        )

        progress.attempts_count = update.attempts_count
        progress.best_passed_tests = update.best_passed_tests
        progress.best_total_tests = update.best_total_tests
        progress.best_ratio = update.best_ratio
        if update.improved:
            progress.best_progress_submission = submission
        if update.first_pass_earned:
            progress.first_passed_at = progress.first_passed_at or timezone.now()
            progress.first_pass_submission = progress.first_pass_submission or submission

        unlocked_rewards = [
            reward_factory(
                milestone_key=reward.milestone_key,
                label=reward.label,
                xp_awarded=reward.xp_awarded,
            )
            for reward in update.unlocked_rewards
        ]

        progress.awarded_progress_markers = list(update.awarded_progress_markers)
        progress.xp_awarded_total = update.xp_awarded_total
        progress.save()

        if update.xp_awarded:
            locked_user.xp_total += update.xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        submission.xp_awarded = update.xp_awarded
        submission.unlocked_progress_rewards = [asdict(reward) for reward in unlocked_rewards]
        submission.save(update_fields=['xp_awarded', 'unlocked_progress_rewards', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, update.xp_awarded
