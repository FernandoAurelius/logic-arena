from django.db import migrations


MISSING_EXERCISE_MAP = {
    'media-aprovacao': ('fundamentos', 'condicionais-basicas'),
}


def backfill_taxonomy(apps, schema_editor):
    Exercise = apps.get_model('arena', 'Exercise')
    ExerciseCategory = apps.get_model('arena', 'ExerciseCategory')
    ExerciseTrack = apps.get_model('arena', 'ExerciseTrack')

    for slug, (category_slug, track_slug) in MISSING_EXERCISE_MAP.items():
        category = ExerciseCategory.objects.filter(slug=category_slug).first()
        track = ExerciseTrack.objects.filter(slug=track_slug).first()
        if category and track:
            Exercise.objects.filter(slug=slug).update(category=category, track=track)


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0007_exercisecategory_exercisetrack_and_taxonomy'),
    ]

    operations = [
        migrations.RunPython(backfill_taxonomy, migrations.RunPython.noop),
    ]
