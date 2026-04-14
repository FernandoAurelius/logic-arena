from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0002_submission_feedback_payload_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='feedback_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('ready', 'Ready'), ('error', 'Error')],
                default='pending',
                max_length=20,
            ),
        ),
    ]
