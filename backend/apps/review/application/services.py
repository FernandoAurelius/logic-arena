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
    project_files: dict[str, str] | None,
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
                project_files=project_files,
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


def review_submission_chat_response(
    submission: Submission,
    user_message: str,
    history: list[dict[str, str]],
    *,
    project_files: dict[str, str] | None = None,
) -> str:
    return arena_review_submission_chat(
        exercise_title=submission.exercise.title,
        statement=submission.exercise.statement,
        source_code=submission.source_code,
        project_files=project_files,
        console_output=submission.console_output,
        feedback_summary=submission.feedback,
        user_message=user_message,
        history=history,
    )


def review_evaluation_chat_response(evaluation_run, user_message: str, history: list[dict[str, str]]) -> str:
    legacy_submission = evaluation_run.legacy_submission
    evidence_bundle = evaluation_run.evidence_bundle or {}
    project_files = evidence_bundle.get('files') if isinstance(evidence_bundle.get('files'), dict) else None
    if legacy_submission is not None:
        return review_submission_chat_response(
            legacy_submission,
            user_message,
            history,
            project_files=project_files,
        )

    evaluator_results = evaluation_run.evaluator_results or {}
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

    if family_key == 'restricted_code':
        template = evaluator_results.get('template') or evidence_bundle.get('workspace_spec', {}).get('template')
        criteria_results = evaluator_results.get('criteria_results') or evidence_bundle.get('criteria_results') or []
        passed_criteria = [
            criterion.get('label')
            for criterion in criteria_results
            if criterion.get('passed') and criterion.get('label')
        ]
        failed_criteria = [
            criterion.get('label')
            for criterion in criteria_results
            if not criterion.get('passed') and criterion.get('label')
        ]
        lines = [
            '### Revisão estrutural',
            f"Template avaliado: {template or 'restricted-code'}",
            (
                f"Critérios atendidos: "
                f"{evaluator_results.get('matched_criteria', 0)}/{evaluator_results.get('total_criteria', 0)}"
            ),
        ]
        if evaluation_run.verdict == EvaluationRun.VERDICT_PASSED:
            lines.append('A correção satisfez os critérios estruturais configurados para este exercício.')
        elif evaluation_run.verdict == EvaluationRun.VERDICT_PARTIAL:
            lines.append('Há avanço estrutural, mas ainda faltam critérios para fechar a correção.')
        else:
            lines.append('A correção ainda não atende aos critérios mínimos esperados.')

        if passed_criteria:
            lines.append('Critérios já atendidos: ' + ' | '.join(passed_criteria))
        if failed_criteria:
            lines.append('Critérios que ainda falharam: ' + ' | '.join(failed_criteria))

        if user_message.strip():
            lines.extend(
                [
                    '',
                    f'Pergunta do aluno: {user_message.strip()}',
                    'Concentre-se na menor alteração necessária para satisfazer apenas os critérios que ainda falharam.',
                ]
            )

        return '\n'.join(lines).strip()

    if family_key == 'contract_behavior_lab':
        checks = evaluator_results.get('checks') or evidence_bundle.get('checks') or []
        divergences = evidence_bundle.get('divergences') or []
        observed_request = evidence_bundle.get('observed_request') or {}
        observed_response = evidence_bundle.get('observed_response') or {}
        lines = [
            '### Revisão de contrato HTTP',
            (
                f"Checks atendidos: "
                f"{evaluator_results.get('passed_tests', 0)}/{evaluator_results.get('total_tests', 0)}"
            ),
            (
                f"Request observada: "
                f"{observed_request.get('method') or '(método ausente)'} "
                f"{observed_request.get('path') or '(path ausente)'}"
            ),
            f"Status observado: {observed_response.get('status_code')!r}",
        ]
        if evaluation_run.verdict == EvaluationRun.VERDICT_PASSED:
            lines.append('O contrato foi respeitado do request ao body de resposta.')
        elif evaluation_run.verdict == EvaluationRun.VERDICT_PARTIAL:
            lines.append('Há aderência parcial ao contrato, mas ainda existem divergências objetivas.')
        else:
            lines.append('O contrato ainda não foi respeitado nos pontos observáveis principais.')

        failed_checks = [check for check in checks if not check.get('passed')]
        if failed_checks:
            lines.append(
                'Checks que falharam: '
                + ' | '.join(str(check.get('check')) for check in failed_checks if check.get('check'))
            )
        if divergences:
            lines.append('Divergências detectadas: ' + ' | '.join(str(item) for item in divergences))

        if user_message.strip():
            lines.extend(
                [
                    '',
                    f'Pergunta do aluno: {user_message.strip()}',
                    'Compare primeiro o acordo esperado no contrato com o que foi realmente observado, sem pular direto para o body.',
                ]
            )

        return '\n'.join(lines).strip()

    return (
        'Ainda não há uma revisão especializada para esta família. '
        'Use a evidência objetiva desta avaliação como base e retorne depois para uma revisão mais profunda.'
    )
