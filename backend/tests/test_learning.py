import pytest

from learning.application.services import build_module_progress_summary, build_track_progress_summary
from learning.selectors import get_track_by_slug


pytestmark = pytest.mark.django_db


def test_learning_app_exposes_track_detail_and_explanation(client, auth_headers, arena_user, catalog_graph):
    first, second, third = catalog_graph['exercises']
    first.user_progress.create(
        user=arena_user,
        attempts_count=1,
        best_passed_tests=1,
        best_total_tests=1,
        best_ratio=1.0,
        awarded_progress_markers=['passed_once'],
        xp_awarded_total=35,
    )
    second.user_progress.create(
        user=arena_user,
        attempts_count=2,
        best_passed_tests=0,
        best_total_tests=1,
        best_ratio=0.0,
    )

    response = client.get(f"/api/catalog/tracks/{catalog_graph['track'].slug}", **auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload['total_exercises'] == 3
    assert [exercise['position'] for exercise in payload['exercises']] == [1, 2, 3]
    assert [exercise['slug'] for exercise in payload['exercises']] == [first.slug, second.slug, third.slug]
    assert payload['exercises'][0]['progress']['status'] == 'passed'
    assert payload['exercises'][1]['progress']['status'] == 'in_progress'
    assert payload['exercises'][2]['progress']['status'] == 'locked'
    assert payload['current_target_slug'] == second.slug

    explanation_response = client.get(
        f"/api/catalog/tracks/{catalog_graph['track'].slug}/explanations/{second.slug}",
        **auth_headers,
    )
    assert explanation_response.status_code == 200
    explanation = explanation_response.json()
    assert explanation['track_slug'] == catalog_graph['track'].slug
    assert explanation['exercise_slug'] == second.slug
    assert explanation['learning_goal']
    assert explanation['concepts']
    assert explanation['code_examples']


def test_learning_selectors_and_services_retain_track_context(catalog_graph, arena_user):
    track = get_track_by_slug(catalog_graph['track'].slug)
    assert track is not None

    summary = build_track_progress_summary(track, arena_user)
    assert summary['total'] == 3
    module_summary = build_module_progress_summary(catalog_graph['module'], arena_user)
    assert module_summary['total_tracks'] >= 1
