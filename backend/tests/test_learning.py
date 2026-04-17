import pytest

from apps.arena.models import Exercise
from apps.learning.application.services import build_module_progress_summary, build_track_progress_summary
from apps.learning.selectors import get_track_by_slug


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


def test_learning_explanation_for_objective_item_is_editorial(client, auth_headers, catalog_graph):
    track = catalog_graph['track']
    objective = Exercise.objects.create(
        slug='tripe-universitario-teste',
        title='Tripé universitário e visão de formação',
        statement='No material de apresentação da disciplina, a ideia de universidade aparece associada a três pilares. Qual alternativa identifica corretamente esse tripé?',
        learning_objectives=[
            'Reconhecer o tripé universitário apresentado na disciplina.',
            'Distinguir pilares institucionais de modelos pedagógicos.',
        ],
        family_key=Exercise.FAMILY_OBJECTIVE_ITEM,
        difficulty='fácil',
        language='pt-BR',
        category=catalog_graph['category'],
        track=track,
        estimated_time_minutes=2,
        track_position=4,
        concept_summary='O tripé universitário apresentado é ensino, pesquisa e extensão.',
        pedagogical_brief='O professor separa pilares institucionais de modelos pedagógicos.',
        professor_note='Leia com atenção quando a questão estiver falando de pilar institucional.',
        workspace_spec={
            'template': 'single-choice',
            'choice_mode': 'single',
            'allow_multiple': False,
            'options': [
                {
                    'key': 'a',
                    'label': 'a',
                    'text': 'Ensino, pesquisa e extensão.',
                    'explanation': 'Correta. O slide do tripé universitário apresenta exatamente esses três pilares.',
                },
                {
                    'key': 'b',
                    'label': 'b',
                    'text': 'Ensino, estágio e certificação.',
                    'explanation': 'Incorreta. Estágio pode fazer parte da formação, mas não compõe o tripé universitário.',
                },
                {
                    'key': 'c',
                    'label': 'c',
                    'text': 'Conhecimento, habilidade e atitude.',
                    'explanation': 'Incorreta. Essa é a lógica do ensino por competências, não o tripé universitário.',
                },
            ],
        },
        evaluation_plan={
            'mechanism': 'answer_key',
            'template': 'single-choice',
            'correct_options': ['a'],
        },
        misconception_tags=['confunde_tripe_com_competencias'],
    )

    response = client.get(
        f'/api/catalog/tracks/{track.slug}/explanations/{objective.slug}',
        **auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['presentation_mode'] == 'objective_review'
    assert payload['question_focus']
    assert 'código' not in payload['learning_goal'].lower()
    assert payload['answer_rationale']
    assert payload['distractor_rationales']
    assert payload['code_examples'] == []
    assert any(item['marker'] == 'B' for item in payload['distractor_rationales'])
