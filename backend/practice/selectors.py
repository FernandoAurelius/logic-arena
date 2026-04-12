from arena.models import Exercise, Submission


def list_active_exercises():
    return Exercise.objects.filter(is_active=True).select_related('category', 'track', 'track__module', 'exercise_type')


def get_active_exercise_by_slug(slug: str):
    return list_active_exercises().prefetch_related('test_cases').filter(slug=slug).first()


def get_submission_for_user(user, submission_id: int):
    return Submission.objects.select_related('exercise').filter(id=submission_id, user=user).first()


def list_user_submissions(user):
    return user.submissions.select_related('exercise').all()
