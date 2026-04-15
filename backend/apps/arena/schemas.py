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
    learning_objectives: list[str] = []
    family_key: str = 'code_lab'
    difficulty: str = 'iniciante'
    language: str = 'python'
    module_slug: str = ''
    module_name: str = ''
    module_description: str = ''
    module_audience: str = ''
    module_source_kind: str = ''
    category_slug: str = ''
    category_name: str = ''
    track_slug: str = ''
    track_name: str = ''
    exercise_type_slug: str = ''
    estimated_time_minutes: int = 15
    version: int = 1
    content_blocks: list[dict] = []
    workspace_spec: dict = {}
    evaluation_plan: dict = {}
    review_profile: str = 'code_lab_default'
    misconception_tags: list[str] = []
    progression_rules: dict = {}
    track_position: int = 0
    concept_summary: str = ''
    pedagogical_brief: str = ''
    starter_code: str = ''
    sample_input: str = ''
    sample_output: str = ''
    professor_note: str = ''
    test_cases: list[TestCaseInputSchema]


class ExerciseSummarySchema(Schema):
    id: int
    slug: str
    title: str
    learning_objectives: list[str] = []
    family_key: str = 'code_lab'
    difficulty: str
    language: str
    professor_note: str
    exercise_type: str = 'drill-de-implementacao'
    exercise_type_label: str = 'Drill de implementação'
    estimated_time_minutes: int = 15
    concept_summary: str = ''
    track_position: int = 0
    module_slug: str | None = None
    module_name: str | None = None
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
    version: int = 1
    content_blocks: list[dict] = []
    workspace_spec: dict = {}
    evaluation_plan: dict = {}
    review_profile: str = 'code_lab_default'
    misconception_tags: list[str] = []
    progression_rules: dict = {}
    starter_code: str
    sample_input: str
    sample_output: str
    test_cases: list[ExerciseTestCaseSchema]


class SubmissionInputSchema(Schema):
    source_code: str


class PracticeAnswerInputSchema(Schema):
    source_code: str = ''
    selected_options: list[str] = []
    response_text: str = ''
    files: dict = {}


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


class AttemptSessionSchema(Schema):
    id: int
    target_type: str
    exercise_slug: str | None = None
    exercise_title: str | None = None
    assessment_slug: str | None = None
    assessment_title: str | None = None
    family_key: str | None = None
    surface_key: str | None = None
    mode: str
    state: dict
    current_workspace_state: dict
    answer_state: dict
    attempt_status: str
    latest_snapshot: 'SubmissionSnapshotSchema | None' = None
    latest_evaluation: 'EvaluationRunSchema | None' = None
    latest_review: 'AIReviewSchema | None' = None
    xp_awarded: int = 0
    unlocked_progress_rewards: list[ProgressRewardSchema] = []
    exercise_progress: ExerciseProgressSchema | None = None
    user_progress: UserProgressSummarySchema | None = None
    created_at: datetime
    updated_at: datetime


class SessionConfigSchema(Schema):
    exercise: ExerciseDetailSchema
    family_key: str
    surface_key: str
    mode: str
    workspace_spec: dict
    review_profile: str


class SubmissionSnapshotSchema(Schema):
    id: int
    session_id: int
    type: str
    payload: dict
    files: dict
    selected_options: list[str]
    created_at: datetime


class EvaluationRunSchema(Schema):
    id: int
    submission_snapshot_id: int
    normalized_score: float
    verdict: str
    evaluator_results: dict
    evidence_bundle: dict
    misconception_inference: list[str]
    raw_artifacts: dict
    created_at: datetime


class AIReviewSchema(Schema):
    id: int
    evaluation_run_id: int
    profile_key: str
    explanation: str
    next_steps: list[str]
    conversation_thread: list[dict]
    created_at: datetime
    updated_at: datetime


class AttemptEvaluationResponseSchema(Schema):
    session: AttemptSessionSchema
    snapshot: SubmissionSnapshotSchema
    evaluation: EvaluationRunSchema
    review: AIReviewSchema | None = None
    xp_awarded: int = 0
    unlocked_progress_rewards: list[ProgressRewardSchema] = []
    exercise_progress: ExerciseProgressSchema | None = None
    user_progress: UserProgressSummarySchema | None = None


class TrackConceptSchema(Schema):
    title: str
    summary: str
    why_it_matters: str
    common_mistake: str


class ExplanationConceptSchema(Schema):
    title: str
    explanation_text: str
    why_it_matters: str
    common_mistake: str


class ExplanationCodeExampleSchema(Schema):
    title: str
    rationale: str
    language: str
    code: str


class TrackExerciseProgressSchema(Schema):
    status: str
    attempts_count: int
    best_passed_tests: int
    best_total_tests: int
    passed_once: bool


class TrackExerciseSchema(ExerciseSummarySchema):
    position: int
    pedagogical_brief: str
    is_current_target: bool
    progress: TrackExerciseProgressSchema


class TrackSummarySchema(Schema):
    slug: str
    name: str
    module_slug: str | None = None
    module_name: str | None = None
    category_slug: str
    category_name: str
    description: str
    goal: str
    level_label: str
    progress_percent: int
    completed_exercises: int
    total_exercises: int
    current_target_slug: str | None = None
    current_target_title: str | None = None


class NavigatorModuleSchema(Schema):
    slug: str
    name: str
    description: str
    audience: str
    source_kind: str
    status: str
    tracks: list[TrackSummarySchema]


class NavigatorResponseSchema(Schema):
    recommended_module_slug: str | None = None
    recommended_module_name: str | None = None
    recommended_track_slug: str | None = None
    recommended_track_name: str | None = None
    modules: list[NavigatorModuleSchema]


class ModuleDetailSchema(Schema):
    slug: str
    name: str
    description: str
    audience: str
    source_kind: str
    status: str
    progress_percent: int
    completed_tracks: int
    total_tracks: int
    current_target_track_slug: str | None = None
    current_target_track_name: str | None = None
    current_target_exercise_slug: str | None = None
    current_target_exercise_title: str | None = None
    tracks: list[TrackSummarySchema]


class TrackMilestoneSchema(Schema):
    title: str
    summary: str
    requirement_label: str
    unlocked: bool
    remaining_exercises: int


class TrackDetailSchema(Schema):
    slug: str
    name: str
    module_slug: str | None = None
    module_name: str | None = None
    category_slug: str
    category_name: str
    description: str
    goal: str
    level_label: str
    progress_percent: int
    completed_exercises: int
    total_exercises: int
    current_target_slug: str | None = None
    current_target_title: str | None = None
    concept_kicker: str
    concepts: list[TrackConceptSchema]
    prerequisites: list[str]
    exercises: list[TrackExerciseSchema]
    milestone: TrackMilestoneSchema


class ExerciseExplanationSchema(Schema):
    module_slug: str | None = None
    module_name: str | None = None
    track_slug: str
    track_name: str
    track_goal: str
    level_label: str
    exercise_slug: str
    exercise_title: str
    exercise_type_label: str
    estimated_time_minutes: int
    concept_summary: str
    pedagogical_brief: str
    learning_goal: str
    concept_focus_markdown: str
    reading_strategy_markdown: str
    implementation_strategy_markdown: str
    assessment_notes_markdown: str
    common_mistakes: list[str]
    mastery_checklist: list[str]
    prerequisites: list[str]
    concepts: list[ExplanationConceptSchema]
    code_examples: list[ExplanationCodeExampleSchema]


class AssessmentContainerPartSchema(Schema):
    id: int
    title: str
    sort_order: int
    exercise_slug: str | None = None
    scoring_rules: dict = {}
    timing_rules: dict = {}
    reveal_rules: dict = {}


class AssessmentContainerSchema(Schema):
    id: int
    slug: str
    title: str
    mode: str
    scoring_rules: dict = {}
    timing_rules: dict = {}
    reveal_rules: dict = {}
    parts: list[AssessmentContainerPartSchema]


class LearningModuleInputSchema(Schema):
    slug: str
    name: str
    description: str = ''
    audience: str = ''
    source_kind: str = ''
    status: str = 'active'
    sort_order: int = 0


class ExerciseTypeInputSchema(Schema):
    slug: str
    name: str
    description: str = ''
    sort_order: int = 0


class TrackConceptInputSchema(Schema):
    title: str
    summary: str
    why_it_matters: str = ''
    common_mistake: str = ''
    sort_order: int = 0


class TrackPrerequisiteInputSchema(Schema):
    label: str
    sort_order: int = 0


class TrackInputSchema(Schema):
    slug: str
    name: str
    module_slug: str
    category_slug: str
    description: str = ''
    goal: str = ''
    level_label: str = ''
    concept_kicker: str = ''
    milestone_title: str = ''
    milestone_summary: str = ''
    milestone_requirement_label: str = ''
    sort_order: int = 0
    concepts: list[TrackConceptInputSchema] = []
    prerequisites: list[TrackPrerequisiteInputSchema] = []


class TrackUpdateSchema(Schema):
    name: str | None = None
    module_slug: str | None = None
    category_slug: str | None = None
    description: str | None = None
    goal: str | None = None
    level_label: str | None = None
    concept_kicker: str | None = None
    milestone_title: str | None = None
    milestone_summary: str | None = None
    milestone_requirement_label: str | None = None
    sort_order: int | None = None
    concepts: list[TrackConceptInputSchema] | None = None
    prerequisites: list[TrackPrerequisiteInputSchema] | None = None


class ExerciseCatalogUpdateSchema(Schema):
    track_slug: str | None = None
    exercise_type_slug: str | None = None
    estimated_time_minutes: int | None = None
    track_position: int | None = None
    concept_summary: str | None = None
    pedagogical_brief: str | None = None


class CatalogAdminReferenceSchema(Schema):
    modules: list[LearningModuleInputSchema]
    exercise_types: list[ExerciseTypeInputSchema]
    categories: list[dict]
    tracks: list[dict]
