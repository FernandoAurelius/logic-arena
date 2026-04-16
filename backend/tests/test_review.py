import pytest

from apps.arena.models import AIReview, EvaluationRun, Exercise, Submission, SubmissionSnapshot, AttemptSession
from apps.review.interface import api as review_api
from apps.review.application import services as review_services


pytestmark = pytest.mark.django_db


def _make_submission(arena_user, exercise):
    return Submission.objects.create(
        user=arena_user,
        exercise=exercise,
        source_code='print("ok")',
        status=Submission.STATUS_PASSED,
        passed_tests=1,
        total_tests=1,
        console_output='Teste 1: PASSOU',
        feedback='Resumo inicial',
        feedback_status=Submission.FEEDBACK_READY,
        feedback_source='agno-gemini',
        feedback_payload={
            'summary': 'Resumo inicial',
            'strengths': ['Acertou o formato'],
            'issues': [],
            'next_steps': ['Continuar praticando'],
            'source': 'agno-gemini',
        },
        execution_results=[],
        review_chat_history=[
            {
                'role': 'assistant',
                'content': '### Revisão automática\nResumo inicial',
            }
        ],
        xp_awarded=35,
        unlocked_progress_rewards=[],
    )


def _make_evaluation_run(arena_user, exercise):
    legacy_submission = _make_submission(arena_user, exercise)
    attempt_session = AttemptSession.objects.create(
        user=arena_user,
        target_type=AttemptSession.TARGET_EXERCISE,
        exercise=exercise,
        mode=AttemptSession.MODE_PRACTICE,
        state={},
        current_workspace_state={},
        answer_state={},
    )
    snapshot = SubmissionSnapshot.objects.create(
        session=attempt_session,
        type=SubmissionSnapshot.TYPE_SUBMIT,
        payload={'source_code': legacy_submission.source_code},
        legacy_submission=legacy_submission,
    )
    evaluation_run = EvaluationRun.objects.create(
        submission=snapshot,
        legacy_submission=legacy_submission,
        evaluator_results={'mechanism': 'runner_tests'},
        normalized_score=1.0,
        verdict=EvaluationRun.VERDICT_PASSED,
        evidence_bundle={'tests': [{'name': 'Teste 1', 'passed': True}]},
        misconception_inference=[],
        raw_artifacts={},
    )
    review = AIReview.objects.create(
        evaluation_run=evaluation_run,
        profile_key='code_lab_default',
        explanation='Explicação inicial',
        next_steps=['Continuar praticando'],
        conversation_thread=[],
    )
    return evaluation_run, review


def _make_objective_evaluation_run(arena_user, catalog_graph):
    exercise = Exercise.objects.create(
        slug='objective-review-teste',
        title='Revisão Objetiva',
        statement='Qual operador cobre o caso de igualdade e maioridade?',
        family_key=Exercise.FAMILY_OBJECTIVE_ITEM,
        difficulty='iniciante',
        language='python',
        category=catalog_graph['category'],
        track=catalog_graph['track'],
        estimated_time_minutes=5,
        review_profile='objective_item_default',
        evaluation_plan={
            'mechanism': 'objective_key',
            'template': 'single-choice',
            'choice_mode': 'single',
            'correct_options': ['b'],
            'options': [
                {'key': 'a', 'label': '>', 'misconception_tag': 'limiar_incorreto'},
                {'key': 'b', 'label': '>=', 'explanation': 'Inclui o caso de igualdade.'},
            ],
            'passing_score': 1.0,
        },
        progression_rules={},
    )
    attempt_session = AttemptSession.objects.create(
        user=arena_user,
        target_type=AttemptSession.TARGET_EXERCISE,
        exercise=exercise,
        mode=AttemptSession.MODE_PRACTICE,
        state={'family_key': Exercise.FAMILY_OBJECTIVE_ITEM, 'surface_key': 'objective_choices'},
        current_workspace_state={},
        answer_state={'selected_options': ['a']},
    )
    snapshot = SubmissionSnapshot.objects.create(
        session=attempt_session,
        type=SubmissionSnapshot.TYPE_SUBMIT,
        payload={'selected_options': ['a']},
        selected_options=['a'],
    )
    evaluation_run = EvaluationRun.objects.create(
        submission=snapshot,
        evaluator_results={
            'family_key': Exercise.FAMILY_OBJECTIVE_ITEM,
            'mechanism': 'objective_key',
            'choice_mode': 'single',
            'selected_options': ['a'],
            'selected_labels': ['>'],
            'correct_options': ['b'],
            'correct_labels': ['>='],
            'passed': False,
            'exact_match': False,
            'score': 0.0,
            'passing_score': 1.0,
            'option_results': [
                {'key': 'a', 'label': '>', 'canonical_key': 'a', 'selected': True, 'correct': False, 'misconception_tag': 'limiar_incorreto'},
                {'key': 'b', 'label': '>=', 'canonical_key': 'b', 'selected': False, 'correct': True, 'misconception_tag': ''},
            ],
        },
        normalized_score=0.0,
        verdict=EvaluationRun.VERDICT_FAILED,
        evidence_bundle={
            'statement': exercise.statement,
            'selected_labels': ['>'],
            'correct_labels': ['>='],
            'option_results': [
                {'key': 'a', 'label': '>', 'canonical_key': 'a', 'selected': True, 'correct': False, 'misconception_tag': 'limiar_incorreto'},
                {'key': 'b', 'label': '>=', 'canonical_key': 'b', 'selected': False, 'correct': True, 'misconception_tag': ''},
            ],
        },
        misconception_inference=['limiar_incorreto'],
        raw_artifacts={},
    )
    review = AIReview.objects.create(
        evaluation_run=evaluation_run,
        profile_key='objective_item_default',
        explanation='### Revisão objetiva\nVocê selecionou >, mas o gabarito esperado era >=.',
        next_steps=['Revise operadores relacionais.'],
        conversation_thread=[],
    )
    return evaluation_run, review

def test_evaluation_review_endpoint_returns_evaluation_for_owner(client, auth_headers, arena_user, catalog_graph):
    evaluation_run, review = _make_evaluation_run(arena_user, catalog_graph['exercises'][0])

    evaluation_response = client.get(f'/api/review/evaluations/{evaluation_run.id}', **auth_headers)
    assert evaluation_response.status_code == 200
    evaluation_payload = evaluation_response.json()
    assert evaluation_payload['id'] == evaluation_run.id
    assert evaluation_payload['verdict'] == EvaluationRun.VERDICT_PASSED

    review_response = client.get(f'/api/review/evaluations/{evaluation_run.id}/review', **auth_headers)
    assert review_response.status_code == 200
    review_payload = review_response.json()
    assert review_payload['id'] == review.id
    assert review_payload['profile_key'] == 'code_lab_default'


def test_evaluation_review_chat_endpoint_appends_history(client, auth_headers, arena_user, catalog_graph, monkeypatch):
    evaluation_run, review = _make_evaluation_run(arena_user, catalog_graph['exercises'][0])
    monkeypatch.setattr(review_services, 'review_evaluation_chat_response', lambda *args, **kwargs: 'Resposta contextual')
    monkeypatch.setattr(review_api, 'review_evaluation_chat_response', lambda *args, **kwargs: 'Resposta contextual')

    response = client.post(
        f'/api/review/evaluations/{evaluation_run.id}/chat',
        data='{"message":"Qual foi meu erro principal?","history":[]}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 200
    assert response.json()['answer'] == 'Resposta contextual'

    review.refresh_from_db()
    assert review.conversation_thread[-2]['role'] == 'user'
    assert review.conversation_thread[-2]['content'] == 'Qual foi meu erro principal?'
    assert review.conversation_thread[-1]['role'] == 'assistant'
    assert review.conversation_thread[-1]['content'] == 'Resposta contextual'


def test_evaluation_review_chat_endpoint_passes_multifile_project_context(
    client,
    auth_headers,
    arena_user,
    catalog_graph,
    monkeypatch,
):
    evaluation_run, _review = _make_evaluation_run(arena_user, catalog_graph['exercises'][0])
    evaluation_run.evidence_bundle = {
        'files': {
            'main.py': 'from helpers import dobro\nprint(dobro(2))',
            'helpers.py': 'def dobro(valor):\n    return valor * 2\n',
        }
    }
    evaluation_run.save(update_fields=['evidence_bundle'])

    captured = {}

    def fake_review_submission_chat(**kwargs):
        captured.update(kwargs)
        return 'Resposta com contexto multifile'

    monkeypatch.setattr(review_services, 'arena_review_submission_chat', fake_review_submission_chat)
    monkeypatch.setattr(review_api, 'review_evaluation_chat_response', review_services.review_evaluation_chat_response)

    response = client.post(
        f'/api/review/evaluations/{evaluation_run.id}/chat',
        data='{"message":"onde está meu erro?","history":[]}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 200
    assert response.json()['answer'] == 'Resposta com contexto multifile'
    assert captured['project_files']['helpers.py'] == 'def dobro(valor):\n    return valor * 2\n'


def test_evaluation_review_chat_endpoint_supports_objective_item_without_legacy_submission(client, auth_headers, arena_user, catalog_graph):
    evaluation_run, review = _make_objective_evaluation_run(arena_user, catalog_graph)

    evaluation_response = client.get(f'/api/review/evaluations/{evaluation_run.id}', **auth_headers)
    assert evaluation_response.status_code == 200
    assert evaluation_response.json()['verdict'] == EvaluationRun.VERDICT_FAILED

    review_response = client.get(f'/api/review/evaluations/{evaluation_run.id}/review', **auth_headers)
    assert review_response.status_code == 200
    assert review_response.json()['profile_key'] == 'objective_item_default'

    chat_response = client.post(
        f'/api/review/evaluations/{evaluation_run.id}/chat',
        data='{"message":"Qual conceito eu errei?","history":[]}',
        content_type='application/json',
        **auth_headers,
    )
    assert chat_response.status_code == 200
    assert 'Gabarito esperado' in chat_response.json()['answer']
    assert 'Template avaliado' in chat_response.json()['answer']
