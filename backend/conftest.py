import os
import uuid

import pytest
from django.contrib.auth.hashers import make_password
from django.test import Client

from apps.arena.models import (
    ArenaUser,
    AuthSession,
    Exercise,
    ExerciseCategory,
    ExerciseExplanation,
    ExerciseTestCase,
    ExerciseTrack,
    ExerciseTrackConcept,
    ExerciseTrackPrerequisite,
    LearningModule,
)

os.environ.setdefault('GEMINI_API_KEY', 'pytest-dummy-key')


@pytest.fixture

def client():
    return Client()


@pytest.fixture

def arena_user(db):
    return ArenaUser.objects.create(
        nickname='miguel.barreto',
        password_hash=make_password('senha-secreta'),
    )


@pytest.fixture

def auth_session(arena_user):
    return AuthSession.objects.create(user=arena_user, token=uuid.uuid4().hex)


@pytest.fixture

def auth_headers(auth_session):
    return {'HTTP_AUTHORIZATION': f'Bearer {auth_session.token}'}


@pytest.fixture

def catalog_graph(db):
    module = LearningModule.objects.create(
        slug='fundamentos-python-teste',
        name='Fundamentos de Python - Teste',
        description='Módulo base para navegação e exercícios iniciais.',
        audience='Iniciantes',
        source_kind='curado',
        status=LearningModule.STATUS_ACTIVE,
        sort_order=1,
    )
    category = ExerciseCategory.objects.create(
        slug='fundamentos-teste',
        name='Fundamentos - Teste',
        description='Base operacional do catálogo.',
        sort_order=1,
    )
    track = ExerciseTrack.objects.create(
        slug='condicionais-basicas-teste',
        category=category,
        module=module,
        name='Condicionais Básicas',
        description='Leitura e decisão.',
        goal='Classificar corretamente cenários simples.',
        level_label='Iniciante',
        concept_kicker='Padrões de decisão',
        milestone_title='Checkpoint de Precisão',
        milestone_summary='Mini simulação de validação do bloco.',
        milestone_requirement_label='Concluir os exercícios do bloco.',
        sort_order=1,
    )
    ExerciseTrackConcept.objects.create(
        track=track,
        title='Comparação e prioridade',
        summary='Escolher o caminho certo a partir de critérios simples.',
        why_it_matters='É a base para validar o primeiro exercício condicional.',
        common_mistake='Testar o caso geral antes do específico.',
        sort_order=1,
    )
    ExerciseTrackConcept.objects.create(
        track=track,
        title='Leitura e conversão',
        summary='Ler entrada e converter para o tipo certo antes de calcular.',
        why_it_matters='Evita operar string onde deveria haver número.',
        common_mistake='Esquecer o `float` ou `int` na entrada.',
        sort_order=2,
    )
    ExerciseTrackPrerequisite.objects.create(
        track=track,
        label='Leitura atenta do enunciado',
        sort_order=1,
    )
    first = Exercise.objects.create(
        slug='media-com-aprovacao-teste',
        title='Média com Aprovação - Teste',
        statement='Leia duas notas, calcule a média e informe se o aluno foi aprovado ou reprovado.',
        difficulty='iniciante',
        language='python',
        category=category,
        track=track,
        estimated_time_minutes=10,
        track_position=1,
        concept_summary='Leitura, conversão e decisão condicional.',
        pedagogical_brief='Questão clássica de prova.',
        starter_code='nota1 = float(input())\nnota2 = float(input())\n',
        sample_input='5\n2\n',
        sample_output='3.5\nAluno reprovado.',
        professor_note='Questão clássica para verificar lógica condicional simples.',
    )
    second = Exercise.objects.create(
        slug='maior-ou-igual-a-cem-teste',
        title='Maior ou Igual a Cem - Teste',
        statement='Verifique se um valor é maior ou igual a cem.',
        difficulty='iniciante',
        language='python',
        category=category,
        track=track,
        estimated_time_minutes=8,
        track_position=2,
        concept_summary='Comparação simples.',
        pedagogical_brief='Treina operadores relacionais.',
        starter_code='valor = int(input())\n',
        sample_input='100\n',
        sample_output='Pronto.',
        professor_note='Cobra leitura e comparação.',
    )
    third = Exercise.objects.create(
        slug='idade-para-votar-teste',
        title='Idade para Votar - Teste',
        statement='Leia a idade e informe se a pessoa pode votar.',
        difficulty='iniciante',
        language='python',
        category=category,
        track=track,
        estimated_time_minutes=8,
        track_position=3,
        concept_summary='Comparação e decisão.',
        pedagogical_brief='Questão curta de banca.',
        starter_code='idade = int(input())\n',
        sample_input='18\n',
        sample_output='Pode votar.',
        professor_note='Cobra comparação simples.',
    )
    ExerciseTestCase.objects.create(
        exercise=first,
        input_data='5\n2\n',
        expected_output='3.5\nAluno reprovado.',
        is_hidden=False,
    )
    ExerciseTestCase.objects.create(
        exercise=first,
        input_data='5.5\n6.5\n',
        expected_output='6.0\nAluno aprovado.',
        is_hidden=True,
    )
    ExerciseTestCase.objects.create(
        exercise=second,
        input_data='100\n',
        expected_output='Pronto.',
        is_hidden=False,
    )
    ExerciseTestCase.objects.create(
        exercise=third,
        input_data='18\n',
        expected_output='Pode votar.',
        is_hidden=False,
    )
    ExerciseExplanation.objects.create(
        exercise=first,
        learning_goal='Compreender leitura de entrada, cálculo de média e decisão condicional.',
        concept_focus_markdown='Leitura, conversão e decisão condicional.',
        reading_strategy_markdown='Leia primeiro a ordem das entradas, depois a regra da média e por fim o formato da saída.',
        implementation_strategy_markdown='Leitura, cálculo e decisão em blocos curtos.',
        assessment_notes_markdown='A banca costuma cobrar entrada simples, média e mensagem final objetiva.',
        common_mistakes=['Esquecer a conversão numérica', 'Trocar a ordem das mensagens de saída'],
        mastery_checklist=['Ler duas notas', 'Calcular a média', 'Decidir aprovação pela média'],
    )
    explanation = first.explanation
    explanation.concepts.create(
        title='Leitura e conversão',
        explanation_text='Use `float(input())` quando o exercício pedir notas ou valores decimais.',
        why_it_matters='Evita operar string onde deveria haver número.',
        common_mistake='Esquecer o `float` ou `int` na entrada.',
        sort_order=1,
    )
    explanation.concepts.create(
        title='Condição de aprovação',
        explanation_text='A média deve ser comparada com 5 para decidir aprovação ou reprovação.',
        why_it_matters='É a decisão que determina a mensagem final.',
        common_mistake='Inverter a condição ou usar o limiar errado.',
        sort_order=2,
    )
    explanation.code_examples.create(
        title='Solução direta com média e aprovação',
        rationale='Exemplo enxuto que atende ao formato mais comum de prova.',
        language='python',
        code=(
            'nota1 = float(input())\n'
            'nota2 = float(input())\n'
            'media = (nota1 + nota2) / 2\n'
            'print(media)\n'
            'print("Aluno aprovado." if media >= 5 else "Aluno reprovado.")\n'
        ),
        sort_order=1,
    )
    return {
        'module': module,
        'category': category,
        'track': track,
        'exercises': [first, second, third],
    }
