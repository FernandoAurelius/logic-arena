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


class Exercise(TimestampedModel):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=140)
    statement = models.TextField()
    difficulty = models.CharField(max_length=20, default='iniciante')
    language = models.CharField(max_length=20, default='python')
    category = models.ForeignKey(ExerciseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    track = models.ForeignKey(ExerciseTrack, null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    exercise_type = models.ForeignKey('ExerciseType', null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    estimated_time_minutes = models.PositiveIntegerField(default=15)
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

    def __str__(self) -> str:
        return self.title


class ExerciseExplanation(TimestampedModel):
    exercise = models.OneToOneField(Exercise, on_delete=models.CASCADE, related_name='explanation')
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
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='test_cases')
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
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
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
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='user_progress')
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
