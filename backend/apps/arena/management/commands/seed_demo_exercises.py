from django.core.management.base import BaseCommand

from apps.arena.models import Exercise
from apps.arena.schemas import ExerciseCreateSchema, TestCaseInputSchema
from apps.arena.services import create_exercise


class Command(BaseCommand):
    help = 'Cria exercícios demo iniciais para o MVP'

    def handle(self, *args, **options):
        if Exercise.objects.exists():
            self.stdout.write(self.style.WARNING('Seed ignorado: já existem exercícios cadastrados.'))
            return

        create_exercise(
            ExerciseCreateSchema(
                slug='area-triangulo',
                title='Área do Triângulo',
                statement='Leia a base e a altura de um triângulo, calcule a área e exiba o resultado.',
                difficulty='iniciante',
                language='python',
                starter_code='base = float(input())\naltura = float(input())\n\nprint((base * altura) / 2)\n',
                sample_input='1.5\n2.6\n',
                sample_output='1.95',
                professor_note='Questão curta, direta, cobrando leitura de valores e cálculo sem enfeite.',
                test_cases=[
                    TestCaseInputSchema(input_data='1.5\n2.6\n', expected_output='1.95', is_hidden=False),
                    TestCaseInputSchema(input_data='10\n5\n', expected_output='25.0', is_hidden=True),
                ],
            )
        )

        create_exercise(
            ExerciseCreateSchema(
                slug='media-aprovacao',
                title='Média com Aprovação',
                statement='Leia duas notas, calcule a média e informe se o aluno foi aprovado ou reprovado. A aprovação ocorre com média maior ou igual a 5.',
                difficulty='iniciante',
                language='python',
                starter_code='nota1 = float(input())\nnota2 = float(input())\nmedia = (nota1 + nota2) / 2\nprint(media)\nprint("Aluno aprovado." if media >= 5 else "Aluno reprovado.")\n',
                sample_input='5\n2\n',
                sample_output='3.5\nAluno reprovado.',
                professor_note='Questão clássica para verificar lógica condicional simples.',
                test_cases=[
                    TestCaseInputSchema(input_data='5\n2\n', expected_output='3.5\nAluno reprovado.', is_hidden=False),
                    TestCaseInputSchema(input_data='5.5\n6.5\n', expected_output='6.0\nAluno aprovado.', is_hidden=True),
                ],
            )
        )

        self.stdout.write(self.style.SUCCESS('Exercícios demo criados com sucesso.'))
