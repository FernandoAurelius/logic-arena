import json

import pytest
from django.core.management import call_command

from apps.arena.models import Exercise, ExerciseCategory, ExerciseTrack, ExerciseType, LearningModule


pytestmark = pytest.mark.django_db


def test_sync_curated_course_catalog_creates_module_track_and_objective_items(tmp_path):
    source = tmp_path / 'course.json'
    source.write_text(
        json.dumps(
            {
                'course': {
                    'slug': 'curso-teste-intro-cs',
                    'title': 'Curso Teste - Introdução à Computação',
                    'subtitle': 'Revisão objetiva de fundamentos.',
                    'language': 'pt-BR',
                    'module': 'introducao-ciencia-computacao',
                    'track': 'revisao-prova-1-bimestre',
                    'target_exam': 'Prova 1º Bimestre',
                    'audience': 'alunos iniciantes',
                    'source_materials': [
                        {'title': 'Aula 1.pdf', 'type': 'pdf'},
                    ],
                    'learning_outcomes': ['Distinguir antecedentes e gerações.'],
                    'modules': [
                        {
                            'slug': 'contexto-e-antecedentes',
                            'title': 'Módulo 1 - Contexto e antecedentes',
                            'summary': 'Revisão da abertura da disciplina e da história inicial da computação.',
                            'learning_objectives': ['Reconhecer antecedentes da computação.'],
                            'lessons': [
                                {
                                    'slug': 'competencias',
                                    'title': 'Lição 1 - Competências',
                                    'instructional_text': {
                                        'overview': 'Abertura da disciplina com foco em competências.',
                                        'key_points': ['Competência combina conhecimento, habilidade e atitude.'],
                                        'common_mistakes': ['Reduzir competência a conteúdo teórico.'],
                                        'exam_tips': ['Desconfie de alternativas que falam só em conhecimento.'],
                                    },
                                    'exercise_definitions': [
                                        {
                                            'slug': 'm1-l1-ex1',
                                            'title': 'Tripé universitário',
                                            'family_key': 'objective_item',
                                            'difficulty': 'fácil',
                                            'estimated_time_minutes': 2,
                                            'learning_objectives': ['Reconhecer o tripé universitário.'],
                                            'misconception_tags': ['confunde_tripe_com_competencias'],
                                            'review_profile': 'objective_item_default',
                                            'content_blocks': [
                                                {
                                                    'kind': 'statement',
                                                    'title': 'Questão',
                                                    'content': 'Qual alternativa identifica o tripé universitário?',
                                                }
                                            ],
                                            'workspace_spec': {
                                                'surface_key': 'objective_choices',
                                                'workspace_kind': 'objective_form',
                                                'template': 'single-choice',
                                                'choice_mode': 'single',
                                                'allow_multiple': False,
                                                'options': [
                                                    {'key': 'a', 'label': 'a', 'text': 'Ensino, pesquisa e extensão.'},
                                                    {'key': 'b', 'label': 'b', 'text': 'Ensino, estágio e certificação.'},
                                                ],
                                            },
                                            'evaluation_plan': {
                                                'mechanism': 'answer_key',
                                                'template': 'single-choice',
                                                'correct_options': ['a'],
                                                'explanation_style': 'by_alternative',
                                            },
                                            'progression_rules': {'passing_score': 1.0},
                                        }
                                    ],
                                }
                            ],
                            'checkpoint': {
                                'slug': 'checkpoint-modulo-1',
                                'title': 'Checkpoint do módulo 1',
                                'summary': 'Consolidação dos antecedentes.',
                                'exercise_definitions': [
                                    {
                                        'slug': 'm1-cp-ex1',
                                        'title': 'Checkpoint 1',
                                        'family_key': 'objective_item',
                                        'difficulty': 'intermediário',
                                        'estimated_time_minutes': 3,
                                        'learning_objectives': ['Consolidar os antecedentes.'],
                                        'misconception_tags': ['mistura_mecanico_com_eletronico'],
                                        'review_profile': 'objective_item_default',
                                        'content_blocks': [
                                            {
                                                'kind': 'statement',
                                                'title': 'Questão',
                                                'content': 'Selecione todas as afirmações corretas.',
                                            }
                                        ],
                                        'workspace_spec': {
                                            'surface_key': 'objective_choices',
                                            'workspace_kind': 'objective_form',
                                            'template': 'multi-select',
                                            'choice_mode': 'multiple',
                                            'allow_multiple': True,
                                            'options': [
                                                {'key': 'a', 'label': 'a', 'text': 'O ábaco é antecedente histórico.'},
                                                {'key': 'b', 'label': 'b', 'text': 'O ábaco é da quinta geração.'},
                                            ],
                                        },
                                        'evaluation_plan': {
                                            'mechanism': 'answer_key',
                                            'template': 'multi-select',
                                            'correct_options': ['a'],
                                        },
                                        'progression_rules': {'passing_score': 1.0},
                                    }
                                ],
                            },
                        }
                    ],
                    'final_review_exam': {
                        'slug': 'simulado-final',
                        'title': 'Simulado Final',
                        'summary': 'Revisão integrada.',
                        'exercise_definitions': [
                            {
                                'slug': 'sim-final-ex1',
                                'title': 'Simulado 1',
                                'family_key': 'objective_item',
                                'difficulty': 'intermediário',
                                'estimated_time_minutes': 2,
                                'learning_objectives': ['Integrar os conceitos centrais.'],
                                'misconception_tags': ['mistura_linha_do_tempo'],
                                'review_profile': 'objective_item_default',
                                'content_blocks': [
                                    {
                                        'kind': 'statement',
                                        'title': 'Questão',
                                        'content': 'Qual alternativa reúne apenas antecedentes?',
                                    }
                                ],
                                'workspace_spec': {
                                    'surface_key': 'objective_choices',
                                    'workspace_kind': 'objective_form',
                                    'template': 'single-choice',
                                    'choice_mode': 'single',
                                    'allow_multiple': False,
                                    'options': [
                                        {'key': 'a', 'label': 'a', 'text': 'Ábaco e Pascal.'},
                                        {'key': 'b', 'label': 'b', 'text': 'ENIAC e SSD.'},
                                    ],
                                },
                                'evaluation_plan': {
                                    'mechanism': 'answer_key',
                                    'template': 'single-choice',
                                    'correct_options': ['a'],
                                },
                                'progression_rules': {'passing_score': 1.0},
                            }
                        ],
                    },
                }
            },
            ensure_ascii=False,
        )
    )

    call_command('sync_curated_course_catalog', source=str(source), replace=True)

    module = LearningModule.objects.get(slug='introducao-ciencia-computacao')
    category = ExerciseCategory.objects.get(slug='fundamentos-da-computacao')
    review_type = ExerciseType.objects.get(slug='revisao-objetiva')
    checkpoint_type = ExerciseType.objects.get(slug='checkpoint-de-revisao')
    final_type = ExerciseType.objects.get(slug='simulado-final')

    assert module.name == 'Introdução à Computação'
    assert category.name == 'Fundamentos da Computação'
    assert review_type.name == 'Revisão objetiva'
    assert checkpoint_type.name == 'Checkpoint de revisão'
    assert final_type.name == 'Simulado final'

    track = ExerciseTrack.objects.get(slug='revisao-prova-1-bimestre-contexto-e-antecedentes')
    assert track.module_id == module.id
    assert track.category_id == category.id
    assert track.milestone_title == 'Checkpoint do módulo 1'

    review_exercise = Exercise.objects.get(slug='revisao-prova-1-bimestre-m1-l1-ex1')
    checkpoint_exercise = Exercise.objects.get(slug='revisao-prova-1-bimestre-m1-cp-ex1')
    final_exercise = Exercise.objects.get(slug='revisao-prova-1-bimestre-sim-final-ex1')

    assert review_exercise.family_key == Exercise.FAMILY_OBJECTIVE_ITEM
    assert review_exercise.exercise_type_id == review_type.id
    assert review_exercise.workspace_spec['template'] == 'single-choice'
    assert review_exercise.evaluation_plan['correct_options'] == ['a']
    assert review_exercise.review_profile == 'objective_item_default'
    assert review_exercise.track_position == 1

    assert checkpoint_exercise.exercise_type_id == checkpoint_type.id
    assert checkpoint_exercise.workspace_spec['template'] == 'multi-select'
    assert checkpoint_exercise.track_position == 2

    assert final_exercise.exercise_type_id == final_type.id
    assert final_exercise.track.slug == 'revisao-prova-1-bimestre-simulado-final'
