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
    xp_total: int
    level: int
    xp_into_level: int
    xp_to_next_level: int


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
    category_slug: str = ''
    category_name: str = ''
    track_slug: str = ''
    track_name: str = ''
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
    category_slug: str | None = None
    category_name: str | None = None
    track_slug: str | None = None
    track_name: str | None = None


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


class FeedbackPayloadSchema(Schema):
    summary: str
    strengths: list[str]
    issues: list[str]
    next_steps: list[str]
    source: str


class ReviewChatMessageSchema(Schema):
    role: str
    content: str


class ReviewChatInputSchema(Schema):
    message: str
    history: list[ReviewChatMessageSchema] = []


class ReviewChatResponseSchema(Schema):
    answer: str


class TestResultSchema(Schema):
    index: int
    input_data: str
    expected_output: str
    actual_output: str
    passed: bool
    stderr: str


class ProgressRewardSchema(Schema):
    milestone_key: str
    label: str
    xp_awarded: int


class ExerciseProgressSchema(Schema):
    attempts_count: int
    best_passed_tests: int
    best_total_tests: int
    best_ratio: float
    xp_awarded_total: int
    first_passed_at: datetime | None = None
    awarded_progress_markers: list[str]


class UserProgressSummarySchema(Schema):
    xp_total: int
    level: int
    xp_into_level: int
    xp_to_next_level: int


class SubmissionSchema(Schema):
    id: int
    status: str
    passed_tests: int
    total_tests: int
    source_code: str
    console_output: str
    feedback: str
    feedback_status: str
    feedback_source: str
    feedback_payload: FeedbackPayloadSchema
    review_chat_history: list[ReviewChatMessageSchema]
    created_at: datetime
    results: list[TestResultSchema]
    xp_awarded: int
    unlocked_progress_rewards: list[ProgressRewardSchema]
    exercise_progress: ExerciseProgressSchema
    user_progress: UserProgressSummarySchema


class SubmissionSummarySchema(Schema):
    id: int
    exercise_slug: str
    exercise_title: str
    status: str
    passed_tests: int
    total_tests: int
    feedback_status: str
    feedback_source: str
    created_at: datetime
