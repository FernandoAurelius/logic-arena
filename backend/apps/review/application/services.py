import threading

from django.db import close_old_connections

from apps.arena.feedback import build_feedback_error_payload, generate_feedback, review_submission_chat as arena_review_submission_chat
from apps.arena.models import Submission


def serialize_review_submission(submission: Submission) -> dict:
    from apps.practice.application.services import serialize_submission

    return serialize_submission(submission)


def schedule_submission_feedback(
    submission_id: int,
    exercise_title: str,
    statement: str,
    source_code: str,
    passed_tests: int,
    total_tests: int,
    results: list[dict],
) -> None:
    def job() -> None:
        close_old_connections()
        try:
            feedback_payload = generate_feedback(
                exercise_title=exercise_title,
                statement=statement,
                source_code=source_code,
                passed_tests=passed_tests,
                total_tests=total_tests,
                results=results,
            )
            Submission.objects.filter(id=submission_id).update(
                feedback=feedback_payload.summary,
                feedback_status=Submission.FEEDBACK_READY,
                feedback_source=feedback_payload.source,
                feedback_payload=feedback_payload.model_dump(),
                review_chat_history=[
                    {
                        'role': 'assistant',
                        'content': '\n'.join(
                            [
                                '### Revisão automática',
                                feedback_payload.summary,
                                '',
                                '**Pontos fortes**',
                                *[f"- {item}" for item in feedback_payload.strengths],
                                '',
                                '**Ajustes**',
                                *[f"- {item}" for item in feedback_payload.issues],
                                '',
                                '**Próximos passos**',
                                *[f"- {item}" for item in feedback_payload.next_steps],
                            ]
                        ).strip(),
                    }
                ],
            )
        except Exception as error:
            payload = build_feedback_error_payload(error)
            Submission.objects.filter(id=submission_id).update(
                feedback=payload.summary,
                feedback_status=Submission.FEEDBACK_ERROR,
                feedback_source=payload.source,
                feedback_payload=payload.model_dump(),
                review_chat_history=[
                    {
                        'role': 'assistant',
                        'content': payload.summary,
                    }
                ],
            )
        finally:
            close_old_connections()

    threading.Thread(target=job, daemon=True).start()


def review_submission_chat_response(submission: Submission, user_message: str, history: list[dict[str, str]]) -> str:
    return arena_review_submission_chat(
        exercise_title=submission.exercise.title,
        statement=submission.exercise.statement,
        source_code=submission.source_code,
        console_output=submission.console_output,
        feedback_summary=submission.feedback,
        user_message=user_message,
        history=history,
    )
