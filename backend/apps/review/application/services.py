import threading

from django.db import close_old_connections

from apps.arena.feedback import build_feedback_error_payload, generate_feedback, review_submission_chat as arena_review_submission_chat
from apps.arena.models import AIReview, EvaluationRun, Submission


def serialize_review_submission(submission: Submission) -> dict:
    from apps.practice.application.services import serialize_submission

    return serialize_submission(submission)


def serialize_review_evaluation(evaluation_run) -> dict:
    from apps.practice.application.services import serialize_ai_review, serialize_evaluation_run

    return {
        'evaluation': serialize_evaluation_run(evaluation_run),
        'review': serialize_ai_review(evaluation_run.ai_review) if hasattr(evaluation_run, 'ai_review') else None,
    }


def schedule_submission_feedback(
    submission_id: int,
    exercise_title: str,
    statement: str,
    source_code: str,
    passed_tests: int,
    total_tests: int,
    results: list[dict],
    evaluation_run_id: int | None = None,
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
            if evaluation_run_id is not None:
                AIReview.objects.filter(evaluation_run_id=evaluation_run_id).update(
                    explanation=feedback_payload.summary,
                    next_steps=feedback_payload.next_steps,
                    conversation_thread=[
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
            if evaluation_run_id is not None:
                AIReview.objects.filter(evaluation_run_id=evaluation_run_id).update(
                    explanation=payload.summary,
                    next_steps=[],
                    conversation_thread=[
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


def review_evaluation_chat_response(evaluation_run, user_message: str, history: list[dict[str, str]]) -> str:
    legacy_submission = evaluation_run.legacy_submission
    if legacy_submission is not None:
        return review_submission_chat_response(legacy_submission, user_message, history)

    evaluator_results = evaluation_run.evaluator_results or {}
    evidence_bundle = evaluation_run.evidence_bundle or {}
    family_key = evaluator_results.get('family_key')

    if family_key == 'objective_item':
        selected_labels = evaluator_results.get('selected_labels') or evidence_bundle.get('selected_labels') or []
        correct_labels = evaluator_results.get('correct_labels') or evidence_bundle.get('correct_labels') or []
        option_results = evidence_bundle.get('option_results') or []
        template = evaluator_results.get('template') or evidence_bundle.get('evaluation_plan', {}).get('template')
        choice_mode = evaluator_results.get('choice_mode') or evidence_bundle.get('evaluation_plan', {}).get('choice_mode')
        selected_incorrect = [
            option
            for option in option_results
            if option.get('selected') and not option.get('correct')
        ]
        selected_correct = [
            option
            for option in option_results
            if option.get('selected') and option.get('correct')
        ]

        lines = [
            '### Revisão objetiva',
            f"Template avaliado: {template or 'objective-item'}",
            f"Resposta do aluno: {', '.join(selected_labels) if selected_labels else '(nenhuma opção)'}",
            f"Gabarito esperado: {', '.join(correct_labels) if correct_labels else '(sem gabarito definido)'}",
        ]
        if choice_mode:
            lines.append(f"Modo de seleção: {choice_mode}")

        if evaluation_run.verdict == EvaluationRun.VERDICT_PASSED:
            lines.append('Você acertou a leitura central do enunciado e escolheu a alternativa correta.')
        elif evaluation_run.verdict == EvaluationRun.VERDICT_PARTIAL:
            lines.append('Há acerto parcial, mas a combinação final ainda não fecha com o gabarito completo.')
        else:
            lines.append('A resposta ainda não está alinhada com a regra que decide essa questão.')

        if selected_correct:
            lines.append(
                'Acertos observados: '
                + ', '.join(option.get('label', '') for option in selected_correct if option.get('label'))
            )
        if selected_incorrect:
            wrong_labels = ', '.join(option.get('label', '') for option in selected_incorrect if option.get('label'))
            lines.append(f'Distratores escolhidos: {wrong_labels}')
            wrong_tags = [
                option.get('misconception_tag')
                for option in selected_incorrect
                if option.get('misconception_tag')
            ]
            if wrong_tags:
                lines.append('Conceitos a revisar: ' + ', '.join(dict.fromkeys(wrong_tags)))
        elif evaluation_run.verdict != EvaluationRun.VERDICT_PASSED and correct_labels:
            lines.append('Conceitos a revisar: ' + ', '.join(correct_labels))

        correct_explanations = [
            option.get('explanation')
            for option in option_results
            if option.get('correct') and option.get('explanation')
        ]
        if correct_explanations:
            lines.append('Explicação da alternativa correta: ' + ' | '.join(dict.fromkeys(correct_explanations)))

        wrong_explanations = [
            option.get('explanation')
            for option in selected_incorrect
            if option.get('explanation')
        ]
        if wrong_explanations:
            lines.append('Explicações dos distratores escolhidos: ' + ' | '.join(dict.fromkeys(wrong_explanations)))

        if template == 'compile-runtime-output':
            lines.append('Este template pede que você separe compilação, execução e a saída observada do snippet.')
        elif template == 'behavior-classification':
            lines.append('Este template pede que você classifique o comportamento evidenciado pelo código com precisão.')
        elif template in {'snippet-read-only', 'read-only-snippet', 'snippet-analysis', 'code-snippet'}:
            lines.append('Este template pede leitura atenta de um snippet read-only antes de escolher a resposta.')

        if user_message.strip():
            lines.extend(
                [
                    '',
                    f'Pergunta do aluno: {user_message.strip()}',
                    'O ponto principal aqui é comparar a regra pedida no enunciado com a propriedade que cada alternativa realmente representa.',
                ]
            )

        return '\n'.join(lines).strip()

    return (
        'Ainda não há uma revisão especializada para esta família. '
        'Use a evidência objetiva desta avaliação como base e retorne depois para uma revisão mais profunda.'
    )
