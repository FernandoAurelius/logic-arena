import pytest

from apps.arena.models import Submission
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


def test_review_endpoint_returns_submission_for_owner(client, auth_headers, arena_user, catalog_graph):
    submission = _make_submission(arena_user, catalog_graph['exercises'][0])

    response = client.get(f'/api/submissions/{submission.id}', **auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == submission.id
    assert payload['feedback_status'] == Submission.FEEDBACK_READY
    assert payload['review_chat_history'][0]['role'] == 'assistant'


def test_review_chat_endpoint_appends_history(client, auth_headers, arena_user, catalog_graph, monkeypatch):
    submission = _make_submission(arena_user, catalog_graph['exercises'][0])
    monkeypatch.setattr(review_services, 'review_submission_chat_response', lambda **kwargs: 'Resposta da IA')
    monkeypatch.setattr(review_api, 'review_submission_chat_response', lambda **kwargs: 'Resposta da IA')

    response = client.post(
        f'/api/submissions/{submission.id}/review-chat',
        data='{"message":"Onde posso melhorar?","history":[]}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 200
    assert response.json()['answer'] == 'Resposta da IA'

    submission.refresh_from_db()
    assert submission.review_chat_history[-2]['role'] == 'user'
    assert submission.review_chat_history[-2]['content'] == 'Onde posso melhorar?'
    assert submission.review_chat_history[-1]['role'] == 'assistant'
    assert submission.review_chat_history[-1]['content'] == 'Resposta da IA'
