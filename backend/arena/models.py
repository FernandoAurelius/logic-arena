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


class ExerciseTrack(TimestampedModel):
    category = models.ForeignKey(ExerciseCategory, on_delete=models.CASCADE, related_name='tracks')
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category__sort_order', 'sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class Exercise(TimestampedModel):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=140)
    statement = models.TextField()
    difficulty = models.CharField(max_length=20, default='iniciante')
    language = models.CharField(max_length=20, default='python')
    category = models.ForeignKey(ExerciseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    track = models.ForeignKey(ExerciseTrack, null=True, blank=True, on_delete=models.SET_NULL, related_name='exercises')
    starter_code = models.TextField(blank=True)
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    professor_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


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
