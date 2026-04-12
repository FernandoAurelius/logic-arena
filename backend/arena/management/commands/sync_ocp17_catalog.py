import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from arena.models import (
    ExerciseCategory,
    ExerciseTrack,
    ExerciseTrackConcept,
    ExerciseTrackPrerequisite,
    LearningModule,
)


CATEGORY_DEFINITIONS = {
    'java-fundamentos': {
        'name': 'Java Fundamentos',
        'description': 'Fundamentos de compilação, sintaxe, fluxo e APIs centrais do Java 17.',
        'sort_order': 80,
    },
    'java-oop-e-apis': {
        'name': 'Java OOP e APIs',
        'description': 'Orientação a objetos, abstrações, coleções, generics e streams para OCP 17.',
        'sort_order': 90,
    },
    'java-plataforma-e-runtime': {
        'name': 'Java Plataforma e Runtime',
        'description': 'Exceções, módulos, concorrência, I/O, JDBC e comportamento de runtime.',
        'sort_order': 100,
    },
    'java-certificacao-e-revisao': {
        'name': 'Java Certificação e Revisão',
        'description': 'Estratégia de prova, simulados e revisão final para OCP 17.',
        'sort_order': 110,
    },
}


def category_slug_for_module(module_payload: dict) -> str:
    module_id = int(module_payload.get('module_id', 0))
    difficulty = str(module_payload.get('difficulty', '')).strip().lower()
    slug = str(module_payload.get('slug', '')).strip().lower()

    if difficulty == 'review' or 'mock' in slug or 'review' in slug:
        return 'java-certificacao-e-revisao'
    if module_id <= 5:
        return 'java-fundamentos'
    if module_id <= 10:
        return 'java-oop-e-apis'
    return 'java-plataforma-e-runtime'


def level_label_for_module(module_payload: dict) -> str:
    difficulty = str(module_payload.get('difficulty', '')).strip().lower()
    mapping = {
        'foundation': 'Fundamentos OCP',
        'intermediate': 'Nível intermediário',
        'advanced': 'Nível avançado',
        'review': 'Revisão final',
    }
    return mapping.get(difficulty, 'Preparação OCP')


def concept_kicker_for_module(module_payload: dict) -> str:
    objective_links = module_payload.get('official_objective_links') or []
    if objective_links:
        return f'Objetivos {", ".join(objective_links[:2])}'
    if module_payload.get('difficulty') == 'review':
        return 'Simulados e estratégia'
    return 'Base conceitual OCP 17'


def build_track_payloads(source_payload: dict) -> list[dict]:
    track_payloads: list[dict] = []
    modules = source_payload.get('modules') or []

    for module_payload in modules:
        topics = module_payload.get('topics') or []
        entry_requirements = module_payload.get('entry_requirements') or []
        mastery_checklist = module_payload.get('mastery_checklist') or []
        exit_requirements = module_payload.get('exit_requirements') or []
        project_stage = module_payload.get('project_stage') or {}
        estimated_hours = module_payload.get('estimated_hours') or 0

        concepts = []
        for index, topic in enumerate(topics[:4], start=1):
            common_traps = topic.get('common_traps') or []
            concepts.append(
                {
                    'title': topic.get('name', f'Tópico {index}'),
                    'summary': topic.get('summary', ''),
                    'why_it_matters': module_payload.get('why_this_module_exists', ''),
                    'common_mistake': common_traps[0] if common_traps else 'Responder por memória, sem validar a regra do snippet.',
                    'sort_order': index,
                }
            )

        prerequisites = [
            {
                'label': requirement,
                'sort_order': index,
            }
            for index, requirement in enumerate(entry_requirements[:4], start=1)
        ]

        milestone_summary = project_stage.get('goal') or module_payload.get('why_this_module_exists', '')
        milestone_requirement = exit_requirements[0] if exit_requirements else 'Fechar os pontos centrais desta trilha antes de seguir.'

        track_payloads.append(
            {
                'slug': f"ocp17-{module_payload['slug']}",
                'name': module_payload['title'],
                'category_slug': category_slug_for_module(module_payload),
                'description': module_payload.get('why_this_module_exists', ''),
                'goal': exit_requirements[0] if exit_requirements else module_payload.get('why_this_module_exists', ''),
                'level_label': level_label_for_module(module_payload),
                'concept_kicker': concept_kicker_for_module(module_payload),
                'milestone_title': f"Checkpoint OCP {int(module_payload.get('module_id', 0)) + 1:02d}",
                'milestone_summary': milestone_summary,
                'milestone_requirement_label': milestone_requirement,
                'sort_order': int(module_payload.get('module_id', 0)) + 1,
                'concepts': concepts,
                'prerequisites': prerequisites,
                'estimated_hours': estimated_hours,
                'mastery_checklist': mastery_checklist,
            }
        )

    return track_payloads


class Command(BaseCommand):
    help = 'Sincroniza o módulo Preparatório OCP 17 a partir de um JSON curado de contexto do curso.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            required=True,
            help='Caminho absoluto do JSON de contexto OCP 17.',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Remove trilhas OCP existentes antes de recriar a estrutura nova.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        source_path = Path(options['source']).expanduser()
        if not source_path.exists():
            raise CommandError(f'Arquivo não encontrado: {source_path}')

        try:
            payload = json.loads(source_path.read_text())
        except json.JSONDecodeError as error:
            raise CommandError(f'JSON inválido em {source_path}: {error}') from error

        module, _ = LearningModule.objects.update_or_create(
            slug='preparatorio-ocp-17',
            defaults={
                'name': 'Preparatório OCP 17',
                'description': (
                    'Percurso estruturado de Java SE 17 Developer (1Z0-829), com foco em leitura de snippet, '
                    'resolução exam-like e cobertura progressiva dos objetivos oficiais.'
                ),
                'audience': 'Estudantes em preparação para certificação Java SE 17 Developer',
                'source_kind': 'json-curado',
                'status': LearningModule.STATUS_ACTIVE,
                'sort_order': 5,
            },
        )

        category_lookup = {}
        for slug, category_data in CATEGORY_DEFINITIONS.items():
            category, _ = ExerciseCategory.objects.update_or_create(
                slug=slug,
                defaults=category_data,
            )
            category_lookup[slug] = category

        if options['replace']:
            ExerciseTrack.objects.filter(module=module).delete()

        track_payloads = build_track_payloads(payload)

        created_count = 0
        for track_payload in track_payloads:
            track, created = ExerciseTrack.objects.update_or_create(
                slug=track_payload['slug'],
                defaults={
                    'module': module,
                    'category': category_lookup[track_payload['category_slug']],
                    'name': track_payload['name'],
                    'description': track_payload['description'],
                    'goal': track_payload['goal'],
                    'level_label': track_payload['level_label'],
                    'concept_kicker': track_payload['concept_kicker'],
                    'milestone_title': track_payload['milestone_title'],
                    'milestone_summary': track_payload['milestone_summary'],
                    'milestone_requirement_label': track_payload['milestone_requirement_label'],
                    'sort_order': track_payload['sort_order'],
                },
            )

            ExerciseTrackConcept.objects.filter(track=track).delete()
            if track_payload['concepts']:
                ExerciseTrackConcept.objects.bulk_create(
                    [
                        ExerciseTrackConcept(
                            track=track,
                            title=concept['title'],
                            summary=concept['summary'],
                            why_it_matters=concept['why_it_matters'],
                            common_mistake=concept['common_mistake'],
                            sort_order=concept['sort_order'],
                        )
                        for concept in track_payload['concepts']
                    ]
                )

            ExerciseTrackPrerequisite.objects.filter(track=track).delete()
            if track_payload['prerequisites']:
                ExerciseTrackPrerequisite.objects.bulk_create(
                    [
                        ExerciseTrackPrerequisite(
                            track=track,
                            label=prerequisite['label'],
                            sort_order=prerequisite['sort_order'],
                        )
                        for prerequisite in track_payload['prerequisites']
                    ]
                )

            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Módulo OCP 17 sincronizado com {len(track_payloads)} trilhas ({created_count} novas) a partir de {source_path}.'
            )
        )
