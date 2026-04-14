# Generated manually for Logic Arena taxonomy bootstrap
from django.db import migrations, models
import django.db.models.deletion


CATEGORIES = [
    {
        'slug': 'fundamentos',
        'name': 'Fundamentos',
        'description': 'Entrada, saída, conversões e fórmulas diretas.',
        'sort_order': 1,
        'tracks': [
            {'slug': 'entrada-saida-e-formulas', 'name': 'Entrada, Saída e Fórmulas', 'sort_order': 1},
            {'slug': 'condicionais-basicas', 'name': 'Condicionais Básicas', 'sort_order': 2},
        ],
    },
    {
        'slug': 'controle-de-fluxo',
        'name': 'Controle de Fluxo',
        'description': 'Laços, flags, contadores e acumuladores.',
        'sort_order': 2,
        'tracks': [
            {'slug': 'flags-e-while', 'name': 'Flags e While', 'sort_order': 1},
            {'slug': 'sequencias-e-for', 'name': 'Sequências e For', 'sort_order': 2},
        ],
    },
]


EXERCISE_MAP = {
    'soma-dois-inteiros': ('fundamentos', 'entrada-saida-e-formulas'),
    'area-triangulo': ('fundamentos', 'entrada-saida-e-formulas'),
    'media-duas-notas': ('fundamentos', 'condicionais-basicas'),
    'fahrenheit-celsius': ('fundamentos', 'entrada-saida-e-formulas'),
    'maior-ou-igual-cem': ('fundamentos', 'condicionais-basicas'),
    'calculadora-somar-subtrair': ('fundamentos', 'condicionais-basicas'),
    'par-ou-impar': ('fundamentos', 'condicionais-basicas'),
    'maior-de-dois': ('fundamentos', 'condicionais-basicas'),
    'positivo-nulo-negativo': ('fundamentos', 'condicionais-basicas'),
    'lucro-ou-prejuizo': ('fundamentos', 'condicionais-basicas'),
    'idade-para-votar': ('fundamentos', 'condicionais-basicas'),
    'contar-numeros-flag': ('controle-de-fluxo', 'flags-e-while'),
    'media-turma-flag': ('controle-de-fluxo', 'flags-e-while'),
    'media-dos-pares': ('controle-de-fluxo', 'flags-e-while'),
    'menor-valor-flag': ('controle-de-fluxo', 'flags-e-while'),
    'menor-e-maior-valor': ('controle-de-fluxo', 'flags-e-while'),
    'altura-e-genero': ('controle-de-fluxo', 'flags-e-while'),
    'naturais-vertical-ate-10': ('controle-de-fluxo', 'sequencias-e-for'),
    'naturais-pares-ate-12': ('controle-de-fluxo', 'sequencias-e-for'),
    'naturais-impares-ate-13': ('controle-de-fluxo', 'sequencias-e-for'),
    'multiplos-de-tres-ate-21': ('controle-de-fluxo', 'sequencias-e-for'),
    'ordem-decrescente-7-1': ('controle-de-fluxo', 'sequencias-e-for'),
    'sequencia-inteiros-intervalo': ('controle-de-fluxo', 'sequencias-e-for'),
    'sequencia-crescente-ou-decrescente': ('controle-de-fluxo', 'sequencias-e-for'),
    'media-turma-for': ('controle-de-fluxo', 'sequencias-e-for'),
}


def seed_taxonomy(apps, schema_editor):
    ExerciseCategory = apps.get_model('arena', 'ExerciseCategory')
    ExerciseTrack = apps.get_model('arena', 'ExerciseTrack')
    Exercise = apps.get_model('arena', 'Exercise')

    category_lookup = {}
    track_lookup = {}

    for category_data in CATEGORIES:
        category, _ = ExerciseCategory.objects.get_or_create(
            slug=category_data['slug'],
            defaults={
                'name': category_data['name'],
                'description': category_data['description'],
                'sort_order': category_data['sort_order'],
            },
        )
        category_lookup[category.slug] = category

        for track_data in category_data['tracks']:
            track, _ = ExerciseTrack.objects.get_or_create(
                slug=track_data['slug'],
                defaults={
                    'category': category,
                    'name': track_data['name'],
                    'sort_order': track_data['sort_order'],
                },
            )
            track_lookup[track.slug] = track

    for slug, (category_slug, track_slug) in EXERCISE_MAP.items():
        Exercise.objects.filter(slug=slug).update(
            category=category_lookup[category_slug],
            track=track_lookup[track_slug],
        )


def unseed_taxonomy(apps, schema_editor):
    ExerciseCategory = apps.get_model('arena', 'ExerciseCategory')
    ExerciseTrack = apps.get_model('arena', 'ExerciseTrack')
    Exercise = apps.get_model('arena', 'Exercise')
    Exercise.objects.update(category=None, track=None)
    ExerciseTrack.objects.filter(slug__in=[track['slug'] for category in CATEGORIES for track in category['tracks']]).delete()
    ExerciseCategory.objects.filter(slug__in=[category['slug'] for category in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0006_arenauser_xp_total_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='ExerciseTrack',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracks', to='arena.exercisecategory')),
            ],
            options={'ordering': ['category__sort_order', 'sort_order', 'name']},
        ),
        migrations.AddField(
            model_name='exercise',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exercises', to='arena.exercisecategory'),
        ),
        migrations.AddField(
            model_name='exercise',
            name='track',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exercises', to='arena.exercisetrack'),
        ),
        migrations.RunPython(seed_taxonomy, unseed_taxonomy),
    ]
