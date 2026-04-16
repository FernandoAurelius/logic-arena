from types import SimpleNamespace

from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from arena.http_contracts import evaluate_http_contract
from arena.models import ArenaUser, Exercise, ExerciseCategory, ExerciseTrack, ExerciseTestCase, LearningModule
from arena.services import build_submission_review_context, evaluate_submission


class HttpContractEvaluationTests(SimpleTestCase):
    def test_evaluate_http_contract_reports_expected_diffs(self):
        evaluation = evaluate_http_contract(
            family_key='contract_behavior_lab',
            surface_key='http_contract_lab',
            request_spec={
                'method': 'GET',
                'path': '/health',
                'headers': {'accept': 'application/json'},
                'body': None,
            },
            response_spec={
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'ok': True},
                'body_schema': {
                    'type': 'object',
                    'required': ['ok'],
                    'properties': {'ok': {'type': 'boolean'}},
                },
            },
            submission_payload={
                'response_status': 201,
                'response_headers': {'Content-Type': 'application/json'},
                'response_body': '{"ok": true}',
            },
        )

        self.assertEqual(evaluation.passed_tests, 3)
        self.assertEqual(evaluation.total_tests, 4)
        self.assertEqual(evaluation.status, 'failed')
        self.assertEqual(evaluation.evidence_bundle['family_key'], 'contract_behavior_lab')
        self.assertEqual(evaluation.evidence_bundle['observed_response']['status'], 201)
        self.assertIn('status', [item['check'] for item in evaluation.results])


class ContractBehaviorSubmissionTests(TestCase):
    def setUp(self):
        self.user = ArenaUser.objects.create(nickname='ana', password_hash='hash')
        self.module = LearningModule.objects.create(
            slug='fase6-desenvolvimento-web-com-fastapi',
            name='Desenvolvimento Web com FastAPI',
            status=LearningModule.STATUS_ACTIVE,
        )
        self.category = ExerciseCategory.objects.create(
            slug='fase6-web-backend',
            name='Web Backend',
        )
        self.track = ExerciseTrack.objects.create(
            slug='fase6-contratos-http',
            name='Contratos HTTP',
            category=self.category,
            module=self.module,
        )
        self.exercise = Exercise.objects.create(
            slug='health-contract',
            title='Contrato de Health Check',
            statement='Valide o contrato HTTP esperado para o endpoint de health check.',
            family_key='contract_behavior_lab',
            track=self.track,
            category=self.category,
            workspace_spec={
                'family_key': 'contract_behavior_lab',
                'surface_key': 'http_contract_lab',
                'workspace_kind': 'http_contract',
                'contract': {
                    'request': {
                        'method': 'GET',
                        'path': '/health',
                    },
                    'response': {
                        'status_code': 200,
                        'headers': {'content-type': 'application/json'},
                        'body': {'ok': True},
                        'body_schema': {
                            'type': 'object',
                            'required': ['ok'],
                            'properties': {
                                'ok': {'type': 'boolean'},
                            },
                        },
                    },
                },
            },
            evaluation_plan={
                'family_key': 'contract_behavior_lab',
                'contract': {
                    'request': {
                        'method': 'GET',
                        'path': '/health',
                    },
                    'response': {
                        'status_code': 200,
                        'headers': {'content-type': 'application/json'},
                        'body': {'ok': True},
                        'body_schema': {
                            'type': 'object',
                            'required': ['ok'],
                            'properties': {
                                'ok': {'type': 'boolean'},
                            },
                        },
                    },
                },
            },
        )

    def test_contract_submission_persists_payload_and_evidence(self):
        with patch('arena.services._start_feedback_job', return_value=None):
            submission, results = evaluate_submission(
                self.user,
                self.exercise,
                {
                    'response_status': 200,
                    'response_headers': {'content-type': 'application/json'},
                    'response_body': '{"ok": true}',
                },
            )

        self.assertEqual(submission.submission_payload['response_status'], 200)
        self.assertEqual(submission.evidence_bundle['family_key'], 'contract_behavior_lab')
        self.assertEqual(submission.passed_tests, 4)
        self.assertEqual(submission.total_tests, 4)
        self.assertEqual(len(results), 4)

        review_context = build_submission_review_context(self.exercise, submission, results)
        self.assertEqual(review_context['family_key'], 'contract_behavior_lab')
        self.assertEqual(review_context['submission_payload']['response_status'], 200)
        self.assertIn('workspace_spec', review_context)

    def test_code_lab_submission_still_uses_python_runner_flow(self):
        code_exercise = Exercise.objects.create(
            slug='soma-simples',
            title='Soma Simples',
            statement='Some dois números.',
            family_key='code_lab',
            track=self.track,
            category=self.category,
            starter_code='print(1 + 1)',
        )
        ExerciseTestCase.objects.create(
            exercise=code_exercise,
            input_data='',
            expected_output='2',
            is_hidden=False,
        )
        with patch('arena.services.run_python', return_value=SimpleNamespace(ok=True, stdout='2\n', stderr='')), patch(
            'arena.services._start_feedback_job',
            return_value=None,
        ):
            submission, results = evaluate_submission(
                self.user,
                code_exercise,
                {'source_code': 'print(1 + 1)'},
            )

        self.assertEqual(submission.source_code, 'print(1 + 1)')
        self.assertEqual(submission.evidence_bundle['family_key'], 'code_lab')
        self.assertEqual(submission.passed_tests, 1)
        self.assertEqual(results[0]['passed'], True)
