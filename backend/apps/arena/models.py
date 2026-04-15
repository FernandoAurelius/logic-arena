from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ArenaUser(TimestampedModel):
    nickname = models.CharField(max_length=40, unique=True)
    password_hash = models.CharField(max_length=255)
    xp_total = models.PositiveIntegerField(default=0)
    is_catalog_admin = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.nickname


class AuthSession(TimestampedModel):
    user = models.ForeignKey(ArenaUser, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=64, unique=True)
    last_used_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.user.nickname}:{self.token[:8]}'


class ExerciseCategory(TimestampedModel):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class LearningModule(TimestampedModel):
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    audience = models.CharField(max_length=120, blank=True)
    source_kind = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class ExerciseType(TimestampedModel):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class ExerciseTrack(TimestampedModel):
    category = models.ForeignKey(ExerciseCategory, on_delete=models.CASCADE, related_name='tracks')
    module = models.ForeignKey('LearningModule', null=True, blank=True, on_delete=models.SET_NULL, related_name='tracks')
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    goal = models.TextField(blank=True)
    level_label = models.CharField(max_length=120, blank=True)
    concept_kicker = models.CharField(max_length=120, blank=True)
    milestone_title = models.CharField(max_length=140, blank=True)
    milestone_summary = models.TextField(blank=True)
    milestone_requirement_label = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['module__sort_order', 'category__sort_order', 'sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class ExerciseTrackConcept(TimestampedModel):
    track = models.ForeignKey(ExerciseTrack, on_delete=models.CASCADE, related_name='concepts')
    title = models.CharField(max_length=120)
    summary = models.TextField()
    why_it_matters = models.TextField(blank=True)
    common_mistake = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return f'{self.track.name}: {self.title}'


class ExerciseTrackPrerequisite(TimestampedModel):
    track = models.ForeignKey(ExerciseTrack, on_delete=models.CASCADE, related_name='prerequisites')
    label = models.CharField(max_length=160)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return f'{self.track.name}: {self.label}'


class ExerciseDefinition(TimestampedModel):
    FAMILY_CODE_LAB = 'code_lab'
    FAMILY_OBJECTIVE_ITEM = 'objective_item'
    FAMILY_RESTRICTED_CODE = 'restricted_code'
    FAMILY_CONTRACT_BEHAVIOR_LAB = 'contract_behavior_lab'
    FAMILY_GUIDED_RESPONSE = 'guided_response'
    FAMILY_CHOICES = [
        (FAMILY_CODE_LAB, 'Code lab'),
        (FAMILY_OBJECTIVE_ITEM, 'Objective item'),
        (FAMILY_RESTRICTED_CODE, 'Restricted code'),
        (FAMILY_CONTRACT_BEHAVIOR_LAB, 'Contract and behavior lab'),
        (FAMILY_GUIDED_RESPONSE, 'Guided response'),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=140)
    statement = models.TextField()
    learning_objectives = models.JSONField(default=list, blank=True)
    family_key = models.CharField(max_length=40, choices=FAMILY_CHOICES, default=FAMILY_CODE_LAB)
    difficulty = models.CharField(max_length=20, default='iniciante')
    language = models.CharField(max_length=20, default='python')
    category = models.ForeignKey(ExerciseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    track = models.ForeignKey(ExerciseTrack, null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    exercise_type = models.ForeignKey('ExerciseType', null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    estimated_time_minutes = models.PositiveIntegerField(default=15)
    version = models.PositiveIntegerField(default=1)
    content_blocks = models.JSONField(default=list, blank=True)
    workspace_spec = models.JSONField(default=dict, blank=True)
    evaluation_plan = models.JSONField(default=dict, blank=True)
    review_profile = models.CharField(max_length=80, default='code_lab_default')
    misconception_tags = models.JSONField(default=list, blank=True)
    progression_rules = models.JSONField(default=dict, blank=True)
    track_position = models.PositiveIntegerField(default=0)
    concept_summary = models.TextField(blank=True)
    pedagogical_brief = models.TextField(blank=True)
    starter_code = models.TextField(blank=True)
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    professor_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']
        db_table = 'arena_exercise'

    def __str__(self) -> str:
        return self.title


class ExerciseExplanation(TimestampedModel):
    exercise = models.OneToOneField(ExerciseDefinition, on_delete=models.CASCADE, related_name='explanation')
    learning_goal = models.TextField(blank=True)
    concept_focus_markdown = models.TextField(blank=True)
    reading_strategy_markdown = models.TextField(blank=True)
    implementation_strategy_markdown = models.TextField(blank=True)
    assessment_notes_markdown = models.TextField(blank=True)
    common_mistakes = models.JSONField(default=list, blank=True)
    mastery_checklist = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return f'Explanation: {self.exercise.title}'


class ExerciseExplanationConcept(TimestampedModel):
    explanation = models.ForeignKey(ExerciseExplanation, on_delete=models.CASCADE, related_name='concepts')
    title = models.CharField(max_length=120)
    explanation_text = models.TextField()
    why_it_matters = models.TextField(blank=True)
    common_mistake = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']


class ExerciseExplanationCodeExample(TimestampedModel):
    explanation = models.ForeignKey(ExerciseExplanation, on_delete=models.CASCADE, related_name='code_examples')
    title = models.CharField(max_length=140)
    rationale = models.TextField(blank=True)
    language = models.CharField(max_length=30, default='python')
    code = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']


class ExerciseTestCase(TimestampedModel):
    exercise = models.ForeignKey(ExerciseDefinition, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']


class Submission(TimestampedModel):
    STATUS_PENDING = 'pending'
    STATUS_PASSED = 'passed'
    STATUS_FAILED = 'failed'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PASSED, 'Passed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_ERROR, 'Error'),
    ]
    FEEDBACK_PENDING = 'pending'
    FEEDBACK_READY = 'ready'
    FEEDBACK_ERROR = 'error'
    FEEDBACK_STATUS_CHOICES = [
        (FEEDBACK_PENDING, 'Pending'),
        (FEEDBACK_READY, 'Ready'),
        (FEEDBACK_ERROR, 'Error'),
    ]

    user = models.ForeignKey(ArenaUser, on_delete=models.CASCADE, related_name='submissions')
    exercise = models.ForeignKey(ExerciseDefinition, on_delete=models.CASCADE, related_name='submissions')
    source_code = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    passed_tests = models.PositiveIntegerField(default=0)
    total_tests = models.PositiveIntegerField(default=0)
    console_output = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    feedback_status = models.CharField(max_length=20, choices=FEEDBACK_STATUS_CHOICES, default=FEEDBACK_PENDING)
    feedback_source = models.CharField(max_length=30, default='rule-based')
    feedback_payload = models.JSONField(default=dict, blank=True)
    execution_results = models.JSONField(default=list, blank=True)
    review_chat_history = models.JSONField(default=list, blank=True)
    xp_awarded = models.PositiveIntegerField(default=0)
    unlocked_progress_rewards = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']


class UserExerciseProgress(TimestampedModel):
    user = models.ForeignKey(ArenaUser, on_delete=models.CASCADE, related_name='exercise_progress')
    exercise = models.ForeignKey(ExerciseDefinition, on_delete=models.CASCADE, related_name='user_progress')
    attempts_count = models.PositiveIntegerField(default=0)
    last_submission = models.ForeignKey('Submission', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    best_progress_submission = models.ForeignKey('Submission', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    first_pass_submission = models.ForeignKey('Submission', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    best_passed_tests = models.PositiveIntegerField(default=0)
    best_total_tests = models.PositiveIntegerField(default=0)
    best_ratio = models.FloatField(default=0)
    first_passed_at = models.DateTimeField(null=True, blank=True)
    awarded_progress_markers = models.JSONField(default=list, blank=True)
    xp_awarded_total = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['exercise__title']
        unique_together = [('user', 'exercise')]


class AssessmentContainer(TimestampedModel):
    MODE_PRACTICE = 'practice'
    MODE_CHECKPOINT = 'checkpoint'
    MODE_EXAM = 'exam'
    MODE_REVIEW = 'review'
    MODE_CHOICES = [
        (MODE_PRACTICE, 'Practice'),
        (MODE_CHECKPOINT, 'Checkpoint'),
        (MODE_EXAM, 'Exam'),
        (MODE_REVIEW, 'Review'),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_PRACTICE)
    scoring_rules = models.JSONField(default=dict, blank=True)
    timing_rules = models.JSONField(default=dict, blank=True)
    reveal_rules = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class AssessmentContainerPart(TimestampedModel):
    container = models.ForeignKey(AssessmentContainer, on_delete=models.CASCADE, related_name='parts')
    exercise = models.ForeignKey(ExerciseDefinition, null=True, blank=True, on_delete=models.CASCADE, related_name='assessment_parts')
    title = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    scoring_rules = models.JSONField(default=dict, blank=True)
    timing_rules = models.JSONField(default=dict, blank=True)
    reveal_rules = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['sort_order', 'id']


class AttemptSession(TimestampedModel):
    TARGET_EXERCISE = 'exercise'
    TARGET_ASSESSMENT = 'assessment'
    TARGET_TYPE_CHOICES = [
        (TARGET_EXERCISE, 'Exercise'),
        (TARGET_ASSESSMENT, 'Assessment'),
    ]
    MODE_PRACTICE = 'practice'
    MODE_CHECKPOINT = 'checkpoint'
    MODE_EXAM = 'exam'
    MODE_REVIEW = 'review'
    MODE_CHOICES = AssessmentContainer.MODE_CHOICES
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_ABANDONED = 'abandoned'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_ABANDONED, 'Abandoned'),
    ]

    user = models.ForeignKey(ArenaUser, on_delete=models.CASCADE, related_name='attempt_sessions')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES, default=TARGET_EXERCISE)
    exercise = models.ForeignKey(ExerciseDefinition, null=True, blank=True, on_delete=models.CASCADE, related_name='attempt_sessions')
    assessment = models.ForeignKey(AssessmentContainer, null=True, blank=True, on_delete=models.CASCADE, related_name='attempt_sessions')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_PRACTICE)
    state = models.JSONField(default=dict, blank=True)
    current_workspace_state = models.JSONField(default=dict, blank=True)
    answer_state = models.JSONField(default=dict, blank=True)
    attempt_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        ordering = ['-created_at']


class SubmissionSnapshot(TimestampedModel):
    TYPE_RUN = 'run'
    TYPE_CHECK = 'check'
    TYPE_SUBMIT = 'submit'
    TYPE_CHOICES = [
        (TYPE_RUN, 'Run'),
        (TYPE_CHECK, 'Check'),
        (TYPE_SUBMIT, 'Submit'),
    ]

    session = models.ForeignKey(AttemptSession, on_delete=models.CASCADE, related_name='snapshots')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    payload = models.JSONField(default=dict, blank=True)
    files = models.JSONField(default=dict, blank=True)
    selected_options = models.JSONField(default=list, blank=True)
    legacy_submission = models.ForeignKey(Submission, null=True, blank=True, on_delete=models.SET_NULL, related_name='snapshots')

    class Meta:
        ordering = ['created_at', 'id']


class EvaluationRun(TimestampedModel):
    VERDICT_PASSED = 'passed'
    VERDICT_FAILED = 'failed'
    VERDICT_PARTIAL = 'partial'
    VERDICT_ERROR = 'error'
    VERDICT_CHOICES = [
        (VERDICT_PASSED, 'Passed'),
        (VERDICT_FAILED, 'Failed'),
        (VERDICT_PARTIAL, 'Partial'),
        (VERDICT_ERROR, 'Error'),
    ]

    submission = models.ForeignKey(SubmissionSnapshot, on_delete=models.CASCADE, related_name='evaluation_runs')
    evaluator_results = models.JSONField(default=dict, blank=True)
    normalized_score = models.FloatField(default=0)
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES, default=VERDICT_FAILED)
    evidence_bundle = models.JSONField(default=dict, blank=True)
    misconception_inference = models.JSONField(default=list, blank=True)
    raw_artifacts = models.JSONField(default=dict, blank=True)
    legacy_submission = models.ForeignKey(Submission, null=True, blank=True, on_delete=models.SET_NULL, related_name='evaluation_runs')

    class Meta:
        ordering = ['-created_at']


class AIReview(TimestampedModel):
    evaluation_run = models.OneToOneField(EvaluationRun, on_delete=models.CASCADE, related_name='ai_review')
    profile_key = models.CharField(max_length=80)
    explanation = models.TextField(blank=True)
    next_steps = models.JSONField(default=list, blank=True)
    conversation_thread = models.JSONField(default=list, blank=True)


# Temporary compatibility alias while the rest of the codebase migrates to the
# new domain language.
Exercise = ExerciseDefinition
