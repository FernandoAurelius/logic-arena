from apps.progress.domain import (
    PASSED_ONCE_MARKER,
    ProgressStateSnapshot,
    SubmissionSnapshot,
    build_user_progress_summary_from_xp,
    compute_level_from_xp,
    compute_submission_progress_update,
)


def test_progress_domain_computes_levels_and_xp_windows():
    assert compute_level_from_xp(0) == 1
    assert compute_level_from_xp(99) == 1
    assert compute_level_from_xp(100) == 2

    summary = build_user_progress_summary_from_xp(135)
    assert summary == {
        'xp_total': 135,
        'level': 2,
        'xp_into_level': 35,
        'xp_to_next_level': 65,
    }


def test_progress_domain_computes_first_pass_reward_and_best_ratio():
    update = compute_submission_progress_update(
        ProgressStateSnapshot(
            attempts_count=0,
            best_passed_tests=0,
            best_total_tests=0,
            best_ratio=0,
            xp_awarded_total=0,
            awarded_progress_markers=(),
        ),
        SubmissionSnapshot(
            status='passed',
            passed_tests=2,
            total_tests=2,
        ),
    )

    assert update.attempts_count == 1
    assert update.improved is True
    assert update.first_pass_earned is True
    assert update.best_ratio == 1
    assert update.xp_awarded == 35
    assert update.awarded_progress_markers == (PASSED_ONCE_MARKER,)


def test_progress_domain_does_not_award_first_pass_twice():
    update = compute_submission_progress_update(
        ProgressStateSnapshot(
            attempts_count=1,
            best_passed_tests=2,
            best_total_tests=2,
            best_ratio=1,
            xp_awarded_total=35,
            awarded_progress_markers=(PASSED_ONCE_MARKER,),
        ),
        SubmissionSnapshot(
            status='passed',
            passed_tests=2,
            total_tests=2,
        ),
    )

    assert update.attempts_count == 2
    assert update.first_pass_earned is False
    assert update.xp_awarded == 0
