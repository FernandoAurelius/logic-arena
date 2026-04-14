from dataclasses import dataclass


PASSED_ONCE_MARKER = 'passed_once'
PASSED_ONCE_XP = 35


@dataclass(frozen=True)
class ProgressReward:
    milestone_key: str
    label: str
    xp_awarded: int


@dataclass(frozen=True)
class ProgressStateSnapshot:
    attempts_count: int
    best_passed_tests: int
    best_total_tests: int
    best_ratio: float
    xp_awarded_total: int
    awarded_progress_markers: tuple[str, ...]


@dataclass(frozen=True)
class SubmissionSnapshot:
    status: str
    passed_tests: int
    total_tests: int


@dataclass(frozen=True)
class SubmissionProgressUpdate:
    attempts_count: int
    best_passed_tests: int
    best_total_tests: int
    best_ratio: float
    xp_awarded_total: int
    awarded_progress_markers: tuple[str, ...]
    xp_awarded: int
    unlocked_rewards: tuple[ProgressReward, ...]
    improved: bool
    first_pass_earned: bool


def compute_level_from_xp(xp_total: int) -> int:
    return max(1, (xp_total // 100) + 1)


def build_user_progress_summary_from_xp(xp_total: int) -> dict:
    level = compute_level_from_xp(xp_total)
    xp_into_level = xp_total - ((level - 1) * 100)
    return {
        'xp_total': xp_total,
        'level': level,
        'xp_into_level': xp_into_level,
        'xp_to_next_level': max(0, 100 - xp_into_level),
    }


def build_exercise_progress_payload(progress) -> dict:
    return {
        'attempts_count': progress.attempts_count,
        'best_passed_tests': progress.best_passed_tests,
        'best_total_tests': progress.best_total_tests,
        'best_ratio': progress.best_ratio,
        'xp_awarded_total': progress.xp_awarded_total,
        'first_passed_at': progress.first_passed_at,
        'awarded_progress_markers': progress.awarded_progress_markers,
    }


def compute_submission_progress_update(
    progress: ProgressStateSnapshot,
    submission: SubmissionSnapshot,
) -> SubmissionProgressUpdate:
    attempts_count = progress.attempts_count + 1
    total_tests = submission.total_tests
    current_ratio = (submission.passed_tests / total_tests) if total_tests else 0
    improved = (
        current_ratio > progress.best_ratio
        or submission.passed_tests > progress.best_passed_tests
        or (submission.passed_tests == progress.best_passed_tests and total_tests > progress.best_total_tests)
    )

    best_passed_tests = progress.best_passed_tests
    best_total_tests = progress.best_total_tests
    best_ratio = progress.best_ratio

    if improved:
        best_passed_tests = submission.passed_tests
        best_total_tests = total_tests
        best_ratio = current_ratio

    awarded_progress_markers = list(progress.awarded_progress_markers)
    unlocked_rewards: list[ProgressReward] = []
    xp_awarded = 0
    first_pass_earned = False

    if submission.status == 'passed' and PASSED_ONCE_MARKER not in awarded_progress_markers:
        awarded_progress_markers.append(PASSED_ONCE_MARKER)
        unlocked_rewards.append(
            ProgressReward(
                milestone_key=PASSED_ONCE_MARKER,
                label='Primeira aprovação',
                xp_awarded=PASSED_ONCE_XP,
            )
        )
        xp_awarded += PASSED_ONCE_XP
        first_pass_earned = True

    return SubmissionProgressUpdate(
        attempts_count=attempts_count,
        best_passed_tests=best_passed_tests,
        best_total_tests=best_total_tests,
        best_ratio=best_ratio,
        xp_awarded_total=progress.xp_awarded_total + xp_awarded,
        awarded_progress_markers=tuple(awarded_progress_markers),
        xp_awarded=xp_awarded,
        unlocked_rewards=tuple(unlocked_rewards),
        improved=improved,
        first_pass_earned=first_pass_earned,
    )
