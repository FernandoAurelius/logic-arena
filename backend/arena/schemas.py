from datetime import datetime

from ninja import Schema


class ErrorSchema(Schema):
    message: str


class LoginInputSchema(Schema):
    nickname: str
    password: str


class UserSchema(Schema):
    id: int
    nickname: str
    created_at: datetime


class LoginResponseSchema(Schema):
    token: str
    created: bool
    user: UserSchema


class TestCaseInputSchema(Schema):
    input_data: str
    expected_output: str
    is_hidden: bool = True


class ExerciseCreateSchema(Schema):
    slug: str
    title: str
    statement: str
    difficulty: str = 'iniciante'
    language: str = 'python'
    starter_code: str = ''
    sample_input: str = ''
    sample_output: str = ''
    professor_note: str = ''
    test_cases: list[TestCaseInputSchema]


class ExerciseSummarySchema(Schema):
    id: int
    slug: str
    title: str
    difficulty: str
    language: str
    professor_note: str


class ExerciseTestCaseSchema(Schema):
    id: int
    input_data: str
    expected_output: str
    is_hidden: bool


class ExerciseDetailSchema(ExerciseSummarySchema):
    statement: str
    starter_code: str
    sample_input: str
    sample_output: str
    test_cases: list[ExerciseTestCaseSchema]


class SubmissionInputSchema(Schema):
    source_code: str


class TestResultSchema(Schema):
    index: int
    input_data: str
    expected_output: str
    actual_output: str
    passed: bool
    stderr: str


class SubmissionSchema(Schema):
    id: int
    status: str
    passed_tests: int
    total_tests: int
    console_output: str
    feedback: str
    created_at: datetime
    results: list[TestResultSchema]


class SubmissionSummarySchema(Schema):
    id: int
    exercise_slug: str
    exercise_title: str
    status: str
    passed_tests: int
    total_tests: int
    created_at: datetime
