import pytest

from apps.arena.models import Exercise


pytestmark = pytest.mark.django_db


def _create_objective_item_exercise(catalog_graph, *, slug: str):
    return Exercise.objects.create(
        slug=slug,
        title='Objetiva sem run',
        statement='Selecione a alternativa correta.',
        difficulty='intermediário',
        language='python',
        family_key=Exercise.FAMILY_OBJECTIVE_ITEM,
        category=catalog_graph['category'],
        track=catalog_graph['track'],
        estimated_time_minutes=5,
        review_profile='objective_item_default',
        content_blocks=[],
        evaluation_plan={
            'mechanism': 'objective_key',
            'template': 'single-choice',
            'choice_mode': 'single',
            'correct_options': ['a'],
            'options': [
                {'key': 'a', 'label': 'Correta'},
                {'key': 'b', 'label': 'Incorreta'},
            ],
            'passing_score': 1.0,
        },
        misconception_tags=[],
        progression_rules={},
        track_position=99,
        concept_summary='Diagnóstico conceitual.',
        pedagogical_brief='Questão objetiva com evidência explícita.',
        starter_code='',
        sample_input='',
        sample_output='',
        professor_note='',
    )


def test_practice_post_exercise_rejects_unregistered_family(client, auth_headers):
    response = client.post(
        '/api/practice/exercises',
        data=(
            '{"slug":"familia-invalida","title":"Família Inválida","statement":"Teste","family_key":"nao_existe",'
            '"test_cases":[{"input_data":"","expected_output":"","is_hidden":false}]}'
        ),
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 400
    assert response.json()['message'] == 'Família de exercício não registrada: nao_existe'


def test_single_file_code_lab_keeps_single_surface_key(client, auth_headers, catalog_graph):
    exercise = catalog_graph['exercises'][0]
    exercise.workspace_spec = {
        'workspace_kind': 'single_file',
        'entrypoint': 'main.py',
        'files': {'main.py': {'content': 'print("ok")'}},
    }
    exercise.save(update_fields=['workspace_spec'])

    config_response = client.get(f'/api/practice/exercises/{exercise.slug}/session-config', **auth_headers)

    assert config_response.status_code == 200
    assert config_response.json()['surface_key'] == 'code_editor_single'


def test_objective_item_run_returns_400_for_unsupported_snapshot_type(client, auth_headers, catalog_graph):
    exercise = _create_objective_item_exercise(catalog_graph, slug='objective-item-run-invalido')

    session_response = client.post(f'/api/practice/exercises/{exercise.slug}/sessions', **auth_headers)
    assert session_response.status_code == 201

    run_response = client.post(
        f"/api/practice/sessions/{session_response.json()['id']}/run",
        data='{"selected_options":["a"]}',
        content_type='application/json',
        **auth_headers,
    )

    assert run_response.status_code == 400
    assert run_response.json()['message'] == 'Tipo de snapshot "run" não suportado para objective_item.'
