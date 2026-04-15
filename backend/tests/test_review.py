import pytest

from apps.arena.models import AIReview, EvaluationRun, Submission, SubmissionSnapshot, AttemptSession
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
