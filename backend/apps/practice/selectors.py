from apps.arena.models import AssessmentContainer, AttemptSession, Exercise


def list_active_exercises():
    return Exercise.objects.filter(is_active=True).select_related('category', 'track', 'track__module', 'exercise_type')


def get_active_exercise_by_slug(slug: str):
    return list_active_exercises().prefetch_related('test_cases').filter(slug=slug).first()


def get_active_assessment_by_slug(slug: str):
    return AssessmentContainer.objects.filter(is_active=True, slug=slug).prefetch_related('parts', 'parts__exercise').first()


def list_user_attempt_sessions(user):
    return (
        AttemptSession.objects.select_related('exercise', 'assessment')
        .filter(user=user)
        .order_by('-updated_at', '-id')
    )
