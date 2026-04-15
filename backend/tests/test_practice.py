import pytest

from apps.practice.application import services
from apps.arena.models import AssessmentContainer, AssessmentContainerPart, ArenaUser, AttemptSession, Exercise, UserExerciseProgress


pytestmark = pytest.mark.django_db


def _create_objective_item_exercise(
    catalog_graph,
    *,
    slug: str,
    title: str,
    statement: str,
    template: str,
    choice_mode: str,
    correct_options: list[str],
    options: list[dict],
    misconceptions: list[str] | None = None,
):
    return Exercise.objects.create(
        slug=slug,
        title=title,
        statement=statement,
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
            'template': template,
            'choice_mode': choice_mode,
            'correct_options': correct_options,
            'options': options,
            'passing_score': 1.0,
        },
        misconception_tags=misconceptions or [],
        progression_rules={},
        track_position=99,
        concept_summary='Diagnóstico conceitual.',
        pedagogical_brief='Questão objetiva com evidência explícita.',
        starter_code='',
        sample_input='',
        sample_output='',
        professor_note='',
    )


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


def test_practice_can_create_objective_item_with_family_defaults_and_read_only_snippet(client, auth_headers):
    response = client.post(
        '/api/practice/exercises',
        data=(
            '{"slug":"novo-objective-item-practice","title":"Snippet Objetivo","statement":"Leia o snippet e escolha a alternativa correta.",'
            '"family_key":"objective_item","difficulty":"intermediario","language":"python",'
            '"category_slug":"fundamentos-objective","category_name":"Fundamentos Objective","track_slug":"trilha-objective",'
            '"track_name":"Trilha Objective","module_slug":"modulo-objective","module_name":"Modulo Objective",'
            '"exercise_type_slug":"drill-de-implementacao","estimated_time_minutes":6,'
            '"evaluation_plan":{"mechanism":"objective_key","template":"snippet-read-only","choice_mode":"single",'
            '"snippet":"x = 1\\nprint(x)","snippet_language":"python","correct_options":["a"],'
            '"options":[{"key":"a","label":"O snippet imprime 1.","explanation":"A impressão do valor 1 confirma a leitura correta do snippet."},'
            '{"key":"b","label":"O snippet imprime 2.","misconception_tag":"saida_incorreta"}],'
            '"passing_score":1.0},'
            '"content_blocks":[],"test_cases":[]}'
        ),
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload['review_profile'] == 'objective_item_default'
    assert payload['content_blocks'][0]['kind'] == 'statement'
    assert payload['content_blocks'][1]['kind'] == 'snippet'
    assert payload['content_blocks'][1]['read_only'] is True
    assert payload['workspace_spec']['stimulus_kind'] == 'snippet'
    assert payload['workspace_spec']['snippet_read_only'] is True
    assert payload['workspace_spec']['snippet_language'] == 'python'

    config_response = client.get(f"/api/practice/exercises/{payload['slug']}/session-config", **auth_headers)
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload['family_key'] == 'objective_item'
    assert config_payload['surface_key'] == 'objective_choices'
    assert config_payload['workspace_spec']['snippet_read_only'] is True
    assert config_payload['workspace_spec']['stimulus_kind'] == 'snippet'

    session_response = client.post(f"/api/practice/exercises/{payload['slug']}/sessions", **auth_headers)
    assert session_response.status_code == 201
    session_payload = session_response.json()
    assert session_payload['answer_state']['template'] == 'snippet-read-only'
    assert session_payload['answer_state']['choice_mode'] == 'single'

    submit_response = client.post(
        f"/api/practice/sessions/{session_payload['id']}/submit",
        data='{"selected_options":["a"],"response_text":""}',
        content_type='application/json',
        **auth_headers,
    )
    assert submit_response.status_code == 200
    submit_payload = submit_response.json()
    assert submit_payload['evaluation']['verdict'] == 'passed'
    assert 'Explicação da alternativa correta' in submit_payload['review']['explanation']


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


def test_objective_item_single_choice_flow_uses_objective_choices_and_awards_xp(client, auth_headers, arena_user, catalog_graph):
    exercise = _create_objective_item_exercise(
        catalog_graph,
        slug='objective-item-single-choice-teste',
        title='Operador Relacional Correto',
        statement='Qual operador garante que um valor seja maior ou igual ao limite?',
        template='single-choice',
        choice_mode='single',
        correct_options=['b'],
        options=[
            {'key': 'a', 'label': '>', 'misconception_tag': 'limiar_incorreto'},
            {'key': 'b', 'label': '>=', 'explanation': 'É o operador que cobre o caso de igualdade e maioridade.'},
            {'key': 'c', 'label': '==', 'misconception_tag': 'igualdade_incorreta'},
        ],
        misconceptions=['operador_relacional'],
    )

    config_response = client.get(f'/api/practice/exercises/{exercise.slug}/session-config', **auth_headers)
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload['family_key'] == 'objective_item'
    assert config_payload['surface_key'] == 'objective_choices'
    assert config_payload['workspace_spec']['workspace_kind'] == 'objective_form'
    assert len(config_payload['workspace_spec']['options']) == 3

    session_response = client.post(f'/api/practice/exercises/{exercise.slug}/sessions', **auth_headers)
    assert session_response.status_code == 201
    session_payload = session_response.json()
    assert session_payload['answer_state']['selected_options'] == []
    assert session_payload['current_workspace_state']['workspace_kind'] == 'objective_form'

    submit_response = client.post(
        f"/api/practice/sessions/{session_payload['id']}/submit",
        data='{"selected_options":["b"],"response_text":""}',
        content_type='application/json',
        **auth_headers,
    )

    assert submit_response.status_code == 200
    payload = submit_response.json()
    assert payload['evaluation']['verdict'] == 'passed'
    assert payload['evaluation']['normalized_score'] == 1
    assert payload['review']['profile_key'] == 'objective_item_default'
    assert 'Você acertou' in payload['review']['explanation']
    assert payload['xp_awarded'] == 35
    assert ArenaUser.objects.get(pk=arena_user.pk).xp_total == 35

    progress = UserExerciseProgress.objects.get(user=arena_user, exercise=exercise)
    assert progress.attempts_count == 1
    assert progress.xp_awarded_total == 35
    assert progress.awarded_progress_markers == ['passed_once']

    review_chat = client.post(
        f"/api/review/evaluations/{payload['evaluation']['id']}/chat",
        data='{"message":"Por que a resposta certa é essa?","history":[]}',
        content_type='application/json',
        **auth_headers,
    )
    assert review_chat.status_code == 200
    assert 'Gabarito esperado' in review_chat.json()['answer']


def test_objective_item_multi_select_and_classifier_templates_cover_surface_variants(client, auth_headers, catalog_graph):
    multi_select_exercise = _create_objective_item_exercise(
        catalog_graph,
        slug='objective-item-multi-select-teste',
        title='Selecione Todas as Verdades',
        statement='Marque as afirmações corretas sobre comparação relacional.',
        template='multi-select',
        choice_mode='multiple',
        correct_options=['a', 'c'],
        options=[
            {'key': 'a', 'label': 'Comparar números exige converter texto antes.', 'is_correct': True},
            {'key': 'b', 'label': 'Strings sempre se comportam como números.', 'misconception_tag': 'tipo-incorreto'},
            {'key': 'c', 'label': 'Uma resposta objetiva pode ter mais de uma alternativa correta.', 'is_correct': True},
        ],
    )
    classifier_exercise = _create_objective_item_exercise(
        catalog_graph,
        slug='objective-item-classifier-teste',
        title='Classifique o Resultado',
        statement='O snippet entra em contato com um valor antes da chamada do parser.',
        template='compile-runtime-output',
        choice_mode='single',
        correct_options=['runtime-exception'],
        options=[
            {'key': 'compile-error', 'label': 'Compile error', 'misconception_tag': 'compilacao'},
            {'key': 'runtime-exception', 'label': 'Runtime exception', 'explanation': 'A execução falha em tempo de execução.'},
            {'key': 'output', 'label': 'Saída correta', 'misconception_tag': 'saida_incorreta'},
        ],
        misconceptions=['diagnostico-execucao'],
    )

    multi_config = client.get(f'/api/practice/exercises/{multi_select_exercise.slug}/session-config', **auth_headers)
    classifier_config = client.get(f'/api/practice/exercises/{classifier_exercise.slug}/session-config', **auth_headers)
    assert multi_config.status_code == 200
    assert classifier_config.status_code == 200
    assert multi_config.json()['surface_key'] == 'objective_choices'
    assert classifier_config.json()['surface_key'] == 'objective_classifier'
    assert classifier_config.json()['workspace_spec']['template_meta']['key'] == 'compile-runtime-output'
    assert classifier_config.json()['workspace_spec']['template_meta']['analysis_steps']

    multi_session = client.post(f'/api/practice/exercises/{multi_select_exercise.slug}/sessions', **auth_headers)
    classifier_session = client.post(f'/api/practice/exercises/{classifier_exercise.slug}/sessions', **auth_headers)
    assert multi_session.status_code == 201
    assert classifier_session.status_code == 201

    multi_submit = client.post(
        f"/api/practice/sessions/{multi_session.json()['id']}/check",
        data='{"selected_options":["a"],"response_text":""}',
        content_type='application/json',
        **auth_headers,
    )
    classifier_submit = client.post(
        f"/api/practice/sessions/{classifier_session.json()['id']}/submit",
        data='{"selected_options":["compile-error"],"response_text":""}',
        content_type='application/json',
        **auth_headers,
    )

    assert multi_submit.status_code == 200
    assert classifier_submit.status_code == 200

    multi_payload = multi_submit.json()
    classifier_payload = classifier_submit.json()

    assert multi_payload['evaluation']['verdict'] == 'partial'
    assert multi_payload['evaluation']['normalized_score'] == 0.5
    assert 'Conceitos a revisar' in multi_payload['review']['explanation']
    assert classifier_payload['evaluation']['verdict'] == 'failed'
    assert classifier_payload['session']['surface_key'] == 'objective_classifier'
    assert 'Gabarito esperado' in classifier_payload['review']['explanation']


def test_objective_item_compile_runtime_output_can_require_output_text(client, auth_headers, catalog_graph):
    exercise = _create_objective_item_exercise(
        catalog_graph,
        slug='objective-item-output-text-teste',
        title='Classifique e preveja a saída',
        statement='O snippet compila e produz uma saída específica.',
        template='compile-runtime-output',
        choice_mode='single',
        correct_options=['output'],
        options=[
            {'key': 'compile-error', 'label': 'Compile error'},
            {'key': 'runtime-exception', 'label': 'Runtime exception'},
            {'key': 'output', 'label': 'Saída correta', 'is_correct': True},
        ],
    )
    exercise.evaluation_plan = {
        **exercise.evaluation_plan,
        'expected_output_text': '42',
    }
    exercise.save(update_fields=['evaluation_plan', 'updated_at'])

    config_response = client.get(f'/api/practice/exercises/{exercise.slug}/session-config', **auth_headers)
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload['workspace_spec']['template_meta']['requires_output_text'] is True
    assert 'expected_output_text' not in config_payload['workspace_spec']['template_meta']

    session_response = client.post(f'/api/practice/exercises/{exercise.slug}/sessions', **auth_headers)
    assert session_response.status_code == 201
    session_id = session_response.json()['id']

    partial_submit = client.post(
        f'/api/practice/sessions/{session_id}/submit',
        data='{"selected_options":["output"],"response_text":"41"}',
        content_type='application/json',
        **auth_headers,
    )
    assert partial_submit.status_code == 200
    partial_payload = partial_submit.json()
    assert partial_payload['evaluation']['verdict'] == 'partial'
    assert partial_payload['evaluation']['evaluator_results']['output_text_matches'] is False
    assert 'Saída esperada: 42' in partial_payload['review']['explanation']

    second_session = client.post(f'/api/practice/exercises/{exercise.slug}/sessions', **auth_headers)
    assert second_session.status_code == 201
    passed_submit = client.post(
        f"/api/practice/sessions/{second_session.json()['id']}/submit",
        data='{"selected_options":["output"],"response_text":"42"}',
        content_type='application/json',
        **auth_headers,
    )
    assert passed_submit.status_code == 200
    passed_payload = passed_submit.json()
    assert passed_payload['evaluation']['verdict'] == 'passed'
    assert passed_payload['evaluation']['evaluator_results']['output_text_matches'] is True


def test_objective_item_scoring_can_vary_by_mode(client, auth_headers, arena_user, catalog_graph):
    exercise = _create_objective_item_exercise(
        catalog_graph,
        slug='objective-item-scoring-by-mode-teste',
        title='Score por Modo',
        statement='Selecione todas as alternativas corretas.',
        template='multi-select',
        choice_mode='multiple',
        correct_options=['a', 'c'],
        options=[
            {'key': 'a', 'label': 'A alternativa correta 1.', 'is_correct': True},
            {'key': 'b', 'label': 'Distrator relevante.', 'misconception_tag': 'distrator'},
            {'key': 'c', 'label': 'A alternativa correta 2.', 'is_correct': True},
        ],
        misconceptions=['score-por-modo'],
    )
    exercise.evaluation_plan = {
        'mechanism': 'objective_key',
        'template': 'multi-select',
        'choice_mode': 'multiple',
        'correct_options': ['a', 'c'],
        'options': [
            {'key': 'a', 'label': 'A alternativa correta 1.', 'is_correct': True},
            {'key': 'b', 'label': 'Distrator relevante.', 'misconception_tag': 'distrator'},
            {'key': 'c', 'label': 'A alternativa correta 2.', 'is_correct': True},
        ],
        'passing_score': 1.0,
        'scoring_rules': {
            'practice': {'passing_score': 0.5},
            'checkpoint': {'passing_score': 0.8},
            'default': {'passing_score': 1.0},
        },
    }
    exercise.save(update_fields=['evaluation_plan', 'updated_at'])

    practice_result = services.evaluate_objective_selection(
        evaluation_plan=exercise.evaluation_plan,
        content_blocks=[],
        selected_options=['a'],
        response_text='',
        attempt_mode='practice',
    )
    checkpoint_result = services.evaluate_objective_selection(
        evaluation_plan=exercise.evaluation_plan,
        content_blocks=[],
        selected_options=['a'],
        response_text='',
        attempt_mode='checkpoint',
    )

    assert practice_result['normalized_score'] == 0.5
    assert practice_result['passed'] is True
    assert practice_result['score_rule']['passing_score'] == 0.5
    assert checkpoint_result['normalized_score'] == 0.5
    assert checkpoint_result['passed'] is False
    assert checkpoint_result['score_rule']['passing_score'] == 0.8
