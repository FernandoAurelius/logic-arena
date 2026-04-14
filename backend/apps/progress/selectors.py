from apps.arena.models import UserExerciseProgress


def list_user_progress_for_exercises(user, exercises):
    return UserExerciseProgress.objects.filter(
        user=user,
        exercise__in=exercises,
    ).select_related('exercise')

