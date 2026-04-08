from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0004_seed_professor_exercises'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='execution_results',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='submission',
            name='review_chat_history',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
