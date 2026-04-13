import pytest

from progress.application.services import (
    ProgressReward,
    apply_submission_progress,
    build_module_progress_summary,
    build_track_progress_summary,
    build_user_progress_summary,
)
from arena.models import Submission


pytestmark = pytest.mark.django_db


def test_progress_me_endpoint_returns_authenticated_summary(client, auth_headers, arena_user):
    arena_user.xp_total = 135
    arena_user.save(update_fields=['xp_total'])

    response = client.get('/api/progress/me', **auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['xp_total'] == 135
    assert payload['level'] == 2
    assert payload['xp_into_level'] == 35
    assert payload['xp_to_next_level'] == 65


def test_progress_services_build_track_and_module_summary(catalog_graph, arena_user):
    track = catalog_graph['track']
    first = catalog_graph['exercises'][0]
    first.user_progress.create(
        user=arena_user,
        attempts_count=1,
        best_passed_tests=1,
        best_total_tests=1,
        best_ratio=1.0,
        awarded_progress_markers=['passed_once'],
        xp_awarded_total=35,
    )

    track_summary = build_track_progress_summary(track, arena_user)
    module_summary = build_module_progress_summary(catalog_graph['module'], arena_user)
    user_summary = build_user_progress_summary(arena_user)

    assert track_summary['completed'] == 1
    assert track_summary['current_target'] is not None
    assert module_summary['total_tracks'] >= 1
    assert user_summary['level'] >= 1


def test_apply_submission_progress_updates_submission_and_user(catalog_graph, arena_user):
    exercise = catalog_graph['exercises'][0]
    submission = Submission.objects.create(
        user=arena_user,
        exercise=exercise,
        source_code='print(1)',
        status=Submission.STATUS_PASSED,
        passed_tests=1,
        total_tests=1,
        console_output='ok',
        feedback='ok',
        feedback_status=Submission.FEEDBACK_READY,
        feedback_source='test',
        feedback_payload={'summary': 'ok', 'strengths': [], 'issues': [], 'next_steps': [], 'source': 'test'},
        execution_results=[],
        review_chat_history=[],
        xp_awarded=0,
        unlocked_progress_rewards=[],
    )

    progress, rewards, xp_awarded = apply_submission_progress(
        arena_user,
        exercise,
        submission,
        reward_factory=ProgressReward,
    )

    submission.refresh_from_db()
    arena_user.refresh_from_db()

    assert progress.attempts_count == 1
    assert xp_awarded == 35
    assert rewards
    assert submission.xp_awarded == 35
    assert arena_user.xp_total == 35
