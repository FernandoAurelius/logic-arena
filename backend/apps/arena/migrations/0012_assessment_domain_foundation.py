from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0011_seed_learning_modules_and_catalog_metadata'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Exercise',
            new_name='ExerciseDefinition',
        ),
        migrations.AlterModelTable(
            name='exercisedefinition',
            table='arena_exercise',
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='content_blocks',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='evaluation_plan',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='family_key',
            field=models.CharField(
                choices=[
                    ('code_lab', 'Code lab'),
                    ('objective_item', 'Objective item'),
                    ('restricted_code', 'Restricted code'),
                    ('contract_behavior_lab', 'Contract and behavior lab'),
                    ('guided_response', 'Guided response'),
                ],
                default='code_lab',
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='learning_objectives',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='misconception_tags',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='progression_rules',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='review_profile',
            field=models.CharField(default='code_lab_default', max_length=80),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='exercisedefinition',
            name='workspace_spec',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name='AssessmentContainer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(unique=True)),
                ('title', models.CharField(max_length=160)),
                ('mode', models.CharField(choices=[('practice', 'Practice'), ('checkpoint', 'Checkpoint'), ('exam', 'Exam'), ('review', 'Review')], default='practice', max_length=20)),
                ('scoring_rules', models.JSONField(blank=True, default=dict)),
                ('timing_rules', models.JSONField(blank=True, default=dict)),
                ('reveal_rules', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='AttemptSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('target_type', models.CharField(choices=[('exercise', 'Exercise'), ('assessment', 'Assessment')], default='exercise', max_length=20)),
                ('mode', models.CharField(choices=[('practice', 'Practice'), ('checkpoint', 'Checkpoint'), ('exam', 'Exam'), ('review', 'Review')], default='practice', max_length=20)),
                ('state', models.JSONField(blank=True, default=dict)),
                ('current_workspace_state', models.JSONField(blank=True, default=dict)),
                ('answer_state', models.JSONField(blank=True, default=dict)),
                ('attempt_status', models.CharField(choices=[('active', 'Active'), ('completed', 'Completed'), ('abandoned', 'Abandoned')], default='active', max_length=20)),
                ('assessment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attempt_sessions', to='arena.assessmentcontainer')),
                ('exercise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attempt_sessions', to='arena.exercisedefinition')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempt_sessions', to='arena.arenauser')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AssessmentContainerPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(blank=True, max_length=160)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('scoring_rules', models.JSONField(blank=True, default=dict)),
                ('timing_rules', models.JSONField(blank=True, default=dict)),
                ('reveal_rules', models.JSONField(blank=True, default=dict)),
                ('container', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parts', to='arena.assessmentcontainer')),
                ('exercise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assessment_parts', to='arena.exercisedefinition')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SubmissionSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(choices=[('run', 'Run'), ('check', 'Check'), ('submit', 'Submit')], max_length=20)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('files', models.JSONField(blank=True, default=dict)),
                ('selected_options', models.JSONField(blank=True, default=list)),
                ('legacy_submission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='snapshots', to='arena.submission')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='arena.attemptsession')),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='EvaluationRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('evaluator_results', models.JSONField(blank=True, default=dict)),
                ('normalized_score', models.FloatField(default=0)),
                ('verdict', models.CharField(choices=[('passed', 'Passed'), ('failed', 'Failed'), ('partial', 'Partial'), ('error', 'Error')], default='failed', max_length=20)),
                ('evidence_bundle', models.JSONField(blank=True, default=dict)),
                ('misconception_inference', models.JSONField(blank=True, default=list)),
                ('raw_artifacts', models.JSONField(blank=True, default=dict)),
                ('legacy_submission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evaluation_runs', to='arena.submission')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_runs', to='arena.submissionsnapshot')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AIReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile_key', models.CharField(max_length=80)),
                ('explanation', models.TextField(blank=True)),
                ('next_steps', models.JSONField(blank=True, default=list)),
                ('conversation_thread', models.JSONField(blank=True, default=list)),
                ('evaluation_run', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_review', to='arena.evaluationrun')),
            ],
        ),
    ]
