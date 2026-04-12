import pytest

from arena import services
from arena.models import ArenaUser, Submission, UserExerciseProgress


pytestmark = pytest.mark.django_db


def test_submission_awards_xp_on_first_pass_and_updates_progress(client, auth_headers, arena_user, catalog_graph, monkeypatch):
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
    monkeypatch.setattr(services, '_start_feedback_job', lambda *args, **kwargs: None)

    response = client.post(
        f'/api/submissions/exercises/{exercise.slug}/submit',
        data='{"source_code":"nota1 = float(input())\\nnota2 = float(input())\\nmedia = (nota1 + nota2) / 2\\nprint(media)\\nprint(\\"Aluno reprovado.\\")\\n"}',
        content_type='application/json',
        **auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == Submission.STATUS_PASSED
    assert payload['passed_tests'] == 2
    assert payload['xp_awarded'] == 35
    assert payload['feedback_status'] == Submission.FEEDBACK_PENDING
    assert ArenaUser.objects.get(pk=arena_user.pk).xp_total == 35

    progress = UserExerciseProgress.objects.get(user=arena_user, exercise=exercise)
    assert progress.attempts_count == 1
    assert progress.xp_awarded_total == 35
    assert progress.awarded_progress_markers == ['passed_once']
    assert progress.first_pass_submission_id == payload['id']
