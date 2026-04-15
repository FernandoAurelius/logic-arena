from apps.arena.models import AIReview, EvaluationRun, Submission


def get_submission_for_user(user, submission_id: int):
    return Submission.objects.select_related('exercise').filter(id=submission_id, user=user).first()


def get_evaluation_run_for_user(user, evaluation_run_id: int):
    return (
        EvaluationRun.objects.select_related(
            'submission__session__user',
            'submission__session__exercise',
            'legacy_submission',
            'ai_review',
        )
        .filter(id=evaluation_run_id, submission__session__user=user)
        .first()
    )


def get_ai_review_for_user(user, evaluation_run_id: int):
    evaluation_run = get_evaluation_run_for_user(user, evaluation_run_id)
    if evaluation_run is None:
        return None
    return AIReview.objects.filter(evaluation_run=evaluation_run).first()
