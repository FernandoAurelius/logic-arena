from apps.arena.models import Submission


def get_submission_for_user(user, submission_id: int):
    return Submission.objects.select_related('exercise').filter(id=submission_id, user=user).first()
