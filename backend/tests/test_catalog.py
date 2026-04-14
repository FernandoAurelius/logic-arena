import pytest

from apps.catalog.application.services import build_module_progress_summary, build_track_progress_summary
from apps.catalog.selectors import get_track_by_slug, list_active_exercises, list_navigator_modules


pytestmark = pytest.mark.django_db


def test_navigator_returns_grouped_tracks_with_recommendation(client, auth_headers, arena_user, catalog_graph):
    first_exercise = catalog_graph['exercises'][0]
    first_exercise.user_progress.create(
        user=arena_user,
        attempts_count=1,
        best_passed_tests=1,
        best_total_tests=1,
        best_ratio=1.0,
        awarded_progress_markers=['passed_once'],
        xp_awarded_total=35,
    )

    response = client.get('/api/catalog/navigator', **auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['recommended_module_slug'] == catalog_graph['module'].slug
    assert payload['recommended_track_slug'] == catalog_graph['track'].slug
    module = next(module for module in payload['modules'] if module['slug'] == catalog_graph['module'].slug)
    track = next(track for track in module['tracks'] if track['slug'] == catalog_graph['track'].slug)
    assert track['progress_percent'] == 33
    assert track['current_target_title'] == catalog_graph['exercises'][1].title


def test_track_detail_orders_exercises_and_marks_progress_state(client, auth_headers, arena_user, catalog_graph):
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


def test_explanation_endpoint_returns_persisted_content(client, auth_headers, catalog_graph):
    track = catalog_graph['track']
    exercise = catalog_graph['exercises'][1]

    response = client.get(f'/api/catalog/tracks/{track.slug}/explanations/{exercise.slug}', **auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['track_slug'] == track.slug
    assert payload['exercise_slug'] == exercise.slug
    assert payload['learning_goal']
    assert payload['concepts']
    assert payload['code_examples']
    assert any('if' in example['code'] or 'print' in example['code'] for example in payload['code_examples'])


def test_catalog_selectors_and_services_retain_track_context(catalog_graph, arena_user):
    track = get_track_by_slug(catalog_graph['track'].slug)
    assert track is not None
    assert list_active_exercises().filter(track=track).count() == 3

    summary = build_track_progress_summary(track, arena_user)
    assert summary['total'] == 3
    module_summary = build_module_progress_summary(catalog_graph['module'], arena_user)
    assert module_summary['total_tracks'] >= 1
    assert list_navigator_modules().count() >= 1


def test_update_track_rejects_unknown_module_slug(client, auth_headers, arena_user, catalog_graph):
    arena_user.is_catalog_admin = True
    arena_user.save(update_fields=['is_catalog_admin'])

    response = client.patch(
        f"/api/catalog-admin/tracks/{catalog_graph['track'].slug}",
        data='{"module_slug":"modulo-inexistente"}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 404
    assert response.json()['message'] == 'Módulo não encontrado.'


def test_update_exercise_catalog_updates_metadata_without_name_error(client, auth_headers, arena_user, catalog_graph):
    arena_user.is_catalog_admin = True
    arena_user.save(update_fields=['is_catalog_admin'])
    exercise = catalog_graph['exercises'][0]

    response = client.patch(
        f'/api/catalog-admin/exercises/{exercise.slug}/catalog',
        data='{"estimated_time_minutes":14,"concept_summary":"Resumo atualizado","pedagogical_brief":"Brief atualizado"}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['estimated_time_minutes'] == 14
    assert payload['concept_summary'] == 'Resumo atualizado'
    exercise.refresh_from_db()
    assert exercise.pedagogical_brief == 'Brief atualizado'
