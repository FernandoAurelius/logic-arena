import pytest

from apps.practice.application import services
from apps.arena.models import AssessmentContainer, AssessmentContainerPart, ArenaUser, AttemptSession, UserExerciseProgress


pytestmark = pytest.mark.django_db


def test_practice_exercise_endpoints_return_active_catalog(client, auth_headers, catalog_graph):
    exercise = catalog_graph['exercises'][0]

    response = client.get('/api/practice/exercises', **auth_headers)
    assert response.status_code == 200
    assert any(item['slug'] == exercise.slug for item in response.json())

    detail = client.get(f'/api/practice/exercises/{exercise.slug}', **auth_headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload['slug'] == exercise.slug
    assert payload['test_cases']


def test_practice_can_create_exercise_via_post_endpoint(client, auth_headers):
    response = client.post(
        '/api/practice/exercises',
        data=(
            '{"slug":"novo-exercicio-practice","title":"Novo Exercício","statement":"Leia um valor e exiba ele.",'
            '"category_slug":"fundamentos-post","category_name":"Fundamentos Post","track_slug":"trilha-post",'
            '"track_name":"Trilha Post","module_slug":"modulo-post","module_name":"Módulo Post",'
            '"exercise_type_slug":"drill-de-implementacao","test_cases":[{"input_data":"1\\n","expected_output":"1","is_hidden":false}]}'
        ),
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload['slug'] == 'novo-exercicio-practice'
    assert payload['track_slug'] == 'trilha-post'
    assert payload['module_slug'] == 'modulo-post'


def test_submit_session_awards_xp_on_first_pass_and_updates_progress(client, auth_headers, arena_user, catalog_graph, monkeypatch):
    exercise = catalog_graph['exercises'][0]

    def fake_run_python(source_code, stdin):
        if stdin == '5\n2\n':
            return services.ExecutionResult(
                ok=True,
                stdout='3.5\nAluno reprovado.',
                stderr='',
            )
        if stdin == '5.5\n6.5\n':
            return services.ExecutionResult(
                ok=True,
                stdout='6.0\nAluno aprovado.',
                stderr='',
            )
        raise AssertionError(f'Unexpected stdin: {stdin!r}')

    monkeypatch.setattr(services, 'run_python', fake_run_python)
    monkeypatch.setattr(services, 'schedule_submission_feedback', lambda *args, **kwargs: None)

    create_session_response = client.post(f'/api/practice/exercises/{exercise.slug}/sessions', **auth_headers)
    assert create_session_response.status_code == 201
    session_id = create_session_response.json()['id']

    response = client.post(
        f'/api/practice/sessions/{session_id}/submit',
        data='{"source_code":"nota1 = float(input())\\nnota2 = float(input())\\nmedia = (nota1 + nota2) / 2\\nprint(media)\\nprint(\\"Aluno reprovado.\\")\\n"}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['evaluation']['verdict'] == 'passed'
    assert payload['snapshot']['type'] == 'submit'
    assert payload['review']['profile_key'] == 'code_lab_default'
    assert ArenaUser.objects.get(pk=arena_user.pk).xp_total == 35

    progress = UserExerciseProgress.objects.get(user=arena_user, exercise=exercise)
    assert progress.attempts_count == 1
    assert progress.xp_awarded_total == 35
    assert progress.awarded_progress_markers == ['passed_once']
    assert progress.first_pass_submission_id is not None


def test_practice_session_endpoints_expose_new_attempt_contract(client, auth_headers, catalog_graph, monkeypatch):
    exercise = catalog_graph['exercises'][0]

    def fake_run_python(source_code, stdin):
        return services.ExecutionResult(
            ok=True,
            stdout='3.5\nAluno reprovado.',
            stderr='',
        )

    monkeypatch.setattr(services, 'run_python', fake_run_python)
    monkeypatch.setattr(services, 'schedule_submission_feedback', lambda *args, **kwargs: None)

    config_response = client.get(f'/api/practice/exercises/{exercise.slug}/session-config', **auth_headers)
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload['family_key'] == 'code_lab'
    assert config_payload['surface_key'] == 'code_editor_single'

    session_response = client.post(f'/api/practice/exercises/{exercise.slug}/sessions', **auth_headers)
    assert session_response.status_code == 201
    session_payload = session_response.json()
    assert session_payload['target_type'] == 'exercise'
    assert session_payload['exercise_slug'] == exercise.slug

    submit_response = client.post(
        f"/api/practice/sessions/{session_payload['id']}/submit",
        data='{"source_code":"print(\\"ok\\")"}',
        content_type='application/json',
        **auth_headers,
    )

    assert submit_response.status_code == 200
    payload = submit_response.json()
    assert payload['session']['id'] == session_payload['id']
    assert payload['snapshot']['type'] == 'submit'
    assert payload['evaluation']['verdict'] == 'failed'
    assert payload['review']['profile_key'] == 'code_lab_default'
    assert payload['session']['latest_snapshot']['type'] == 'submit'
    assert payload['session']['latest_evaluation']['verdict'] == 'failed'


def test_assessment_endpoints_return_container_and_create_session(client, auth_headers, arena_user, catalog_graph):
    exercise = catalog_graph['exercises'][0]
    assessment = AssessmentContainer.objects.create(
        slug='checkpoint-condicionais-teste',
        title='Checkpoint de Condicionais',
        mode=AssessmentContainer.MODE_CHECKPOINT,
        scoring_rules={'passing_score': 0.7},
        timing_rules={'minutes': 20},
        reveal_rules={'show_feedback': 'after_finish'},
    )
    AssessmentContainerPart.objects.create(
        container=assessment,
        exercise=exercise,
        title='Parte 1',
        sort_order=1,
    )

    detail_response = client.get(f'/api/assessments/{assessment.slug}', **auth_headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload['slug'] == assessment.slug
    assert detail_payload['parts'][0]['exercise_slug'] == exercise.slug

    session_response = client.post(f'/api/assessments/{assessment.slug}/sessions', **auth_headers)
    assert session_response.status_code == 201
    session_payload = session_response.json()
    assert session_payload['target_type'] == AttemptSession.TARGET_ASSESSMENT
    assert session_payload['assessment_slug'] == assessment.slug


def test_practice_sessions_endpoint_returns_canonical_history(client, auth_headers, arena_user, catalog_graph):
    exercise = catalog_graph['exercises'][0]
    AttemptSession.objects.create(
        user=arena_user,
        target_type=AttemptSession.TARGET_EXERCISE,
        exercise=exercise,
        mode=AttemptSession.MODE_PRACTICE,
        state={'family_key': 'code_lab', 'surface_key': 'code_editor_single'},
        current_workspace_state={'entrypoint': 'main.py'},
        answer_state={'source_code': 'print("ok")'},
    )

    response = client.get('/api/practice/sessions', **auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]['exercise_slug'] == exercise.slug
    assert payload[0]['family_key'] == 'code_lab'
    assert payload[0]['surface_key'] == 'code_editor_single'
