from dataclasses import asdict, dataclass

from django.db import transaction
from django.utils import timezone

from arena.models import ArenaUser, Exercise, ExerciseTrack, LearningModule, Submission, UserExerciseProgress
from progress.selectors import list_user_progress_for_exercises

PASSED_ONCE_MARKER = 'passed_once'
PASSED_ONCE_XP = 35


class ProgressRewardFactoryProtocol:
    def __call__(self, milestone_key: str, label: str, xp_awarded: int): ...


@dataclass
class ProgressReward:
    milestone_key: str
    label: str
    xp_awarded: int


def compute_level_from_xp(xp_total: int) -> int:
    return max(1, (xp_total // 100) + 1)


def build_user_progress_summary(user: ArenaUser) -> dict:
    xp_total = user.xp_total
    level = compute_level_from_xp(xp_total)
    xp_into_level = xp_total - ((level - 1) * 100)
    return {
        'xp_total': xp_total,
        'level': level,
        'xp_into_level': xp_into_level,
        'xp_to_next_level': max(0, 100 - xp_into_level),
    }


def build_exercise_progress_payload(progress: UserExerciseProgress) -> dict:
    return {
        'attempts_count': progress.attempts_count,
        'best_passed_tests': progress.best_passed_tests,
        'best_total_tests': progress.best_total_tests,
        'best_ratio': progress.best_ratio,
        'xp_awarded_total': progress.xp_awarded_total,
        'first_passed_at': progress.first_passed_at,
        'awarded_progress_markers': progress.awarded_progress_markers,
    }


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

        progress.attempts_count += 1
        progress.last_submission = submission

        total_tests = submission.total_tests
        current_ratio = (submission.passed_tests / total_tests) if total_tests else 0
        best_ratio = progress.best_ratio or 0
        improved = (
            current_ratio > best_ratio
            or submission.passed_tests > progress.best_passed_tests
            or (submission.passed_tests == progress.best_passed_tests and total_tests > progress.best_total_tests)
        )

        if improved:
            progress.best_passed_tests = submission.passed_tests
            progress.best_total_tests = total_tests
            progress.best_ratio = current_ratio
            progress.best_progress_submission = submission

        awarded_progress_markers = list(progress.awarded_progress_markers or [])
        unlocked_rewards = []
        xp_awarded = 0

        if submission.status == Submission.STATUS_PASSED and PASSED_ONCE_MARKER not in awarded_progress_markers:
            awarded_progress_markers.append(PASSED_ONCE_MARKER)
            unlocked_rewards.append(
                reward_factory(
                    milestone_key=PASSED_ONCE_MARKER,
                    label='Primeira aprovação',
                    xp_awarded=PASSED_ONCE_XP,
                )
            )
            xp_awarded += PASSED_ONCE_XP
            progress.first_passed_at = progress.first_passed_at or timezone.now()
            progress.first_pass_submission = progress.first_pass_submission or submission

        progress.awarded_progress_markers = awarded_progress_markers
        progress.xp_awarded_total += xp_awarded
        progress.save()

        if xp_awarded:
            locked_user.xp_total += xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        submission.xp_awarded = xp_awarded
        submission.unlocked_progress_rewards = [asdict(reward) for reward in unlocked_rewards]
        submission.save(update_fields=['xp_awarded', 'unlocked_progress_rewards', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, xp_awarded
