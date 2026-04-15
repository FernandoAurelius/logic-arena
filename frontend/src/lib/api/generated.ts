import { makeApi, Zodios } from "@zodios/core";
import { z } from "zod";

const authorization = z.union([z.string(), z.null()]).optional();
const TrackConceptSchema = z
  .object({
    title: z.string(),
    summary: z.string(),
    why_it_matters: z.string(),
    common_mistake: z.string(),
  })
  .passthrough();
const TrackExerciseProgressSchema = z
  .object({
    status: z.string(),
    attempts_count: z.number().int(),
    best_passed_tests: z.number().int(),
    best_total_tests: z.number().int(),
    passed_once: z.boolean(),
  })
  .passthrough();
const TrackExerciseSchema = z
  .object({
    id: z.number().int(),
    slug: z.string(),
    title: z.string(),
    learning_objectives: z.array(z.string()).optional().default([]),
    family_key: z.string().optional().default("code_lab"),
    difficulty: z.string(),
    language: z.string(),
    professor_note: z.string(),
    exercise_type: z.string().optional().default("drill-de-implementacao"),
    exercise_type_label: z
      .string()
      .optional()
      .default("Drill de implementação"),
    estimated_time_minutes: z.number().int().optional().default(15),
    concept_summary: z.string().optional().default(""),
    track_position: z.number().int().optional().default(0),
    module_slug: z.union([z.string(), z.null()]).optional(),
    module_name: z.union([z.string(), z.null()]).optional(),
    category_slug: z.union([z.string(), z.null()]).optional(),
    category_name: z.union([z.string(), z.null()]).optional(),
    track_slug: z.union([z.string(), z.null()]).optional(),
    track_name: z.union([z.string(), z.null()]).optional(),
    position: z.number().int(),
    pedagogical_brief: z.string(),
    is_current_target: z.boolean(),
    progress: TrackExerciseProgressSchema,
  })
  .passthrough();
const TrackMilestoneSchema = z
  .object({
    title: z.string(),
    summary: z.string(),
    requirement_label: z.string(),
    unlocked: z.boolean(),
    remaining_exercises: z.number().int(),
  })
  .passthrough();
const TrackDetailSchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    module_slug: z.union([z.string(), z.null()]).optional(),
    module_name: z.union([z.string(), z.null()]).optional(),
    category_slug: z.string(),
    category_name: z.string(),
    description: z.string(),
    goal: z.string(),
    level_label: z.string(),
    progress_percent: z.number().int(),
    completed_exercises: z.number().int(),
    total_exercises: z.number().int(),
    current_target_slug: z.union([z.string(), z.null()]).optional(),
    current_target_title: z.union([z.string(), z.null()]).optional(),
    concept_kicker: z.string(),
    concepts: z.array(TrackConceptSchema),
    prerequisites: z.array(z.string()),
    exercises: z.array(TrackExerciseSchema),
    milestone: TrackMilestoneSchema,
  })
  .passthrough();
const ErrorSchema = z.object({ message: z.string() }).passthrough();
const ExplanationConceptSchema = z
  .object({
    title: z.string(),
    explanation_text: z.string(),
    why_it_matters: z.string(),
    common_mistake: z.string(),
  })
  .passthrough();
const ExplanationCodeExampleSchema = z
  .object({
    title: z.string(),
    rationale: z.string(),
    language: z.string(),
    code: z.string(),
  })
  .passthrough();
const ExerciseExplanationSchema = z
  .object({
    module_slug: z.union([z.string(), z.null()]).optional(),
    module_name: z.union([z.string(), z.null()]).optional(),
    track_slug: z.string(),
    track_name: z.string(),
    track_goal: z.string(),
    level_label: z.string(),
    exercise_slug: z.string(),
    exercise_title: z.string(),
    exercise_type_label: z.string(),
    estimated_time_minutes: z.number().int(),
    concept_summary: z.string(),
    pedagogical_brief: z.string(),
    learning_goal: z.string(),
    concept_focus_markdown: z.string(),
    reading_strategy_markdown: z.string(),
    implementation_strategy_markdown: z.string(),
    assessment_notes_markdown: z.string(),
    common_mistakes: z.array(z.string()),
    mastery_checklist: z.array(z.string()),
    prerequisites: z.array(z.string()),
    concepts: z.array(ExplanationConceptSchema),
    code_examples: z.array(ExplanationCodeExampleSchema),
  })
  .passthrough();
const LoginInputSchema = z
  .object({ nickname: z.string(), password: z.string() })
  .passthrough();
const UserSchema = z
  .object({
    id: z.number().int(),
    nickname: z.string(),
    created_at: z.string().datetime({ offset: true }),
    xp_total: z.number().int(),
    level: z.number().int(),
    xp_into_level: z.number().int(),
    xp_to_next_level: z.number().int(),
  })
  .passthrough();
const LoginResponseSchema = z
  .object({ token: z.string(), created: z.boolean(), user: UserSchema })
  .passthrough();
const ExerciseSummarySchema = z
  .object({
    id: z.number().int(),
    slug: z.string(),
    title: z.string(),
    learning_objectives: z.array(z.string()).optional().default([]),
    family_key: z.string().optional().default("code_lab"),
    difficulty: z.string(),
    language: z.string(),
    professor_note: z.string(),
    exercise_type: z.string().optional().default("drill-de-implementacao"),
    exercise_type_label: z
      .string()
      .optional()
      .default("Drill de implementação"),
    estimated_time_minutes: z.number().int().optional().default(15),
    concept_summary: z.string().optional().default(""),
    track_position: z.number().int().optional().default(0),
    module_slug: z.union([z.string(), z.null()]).optional(),
    module_name: z.union([z.string(), z.null()]).optional(),
    category_slug: z.union([z.string(), z.null()]).optional(),
    category_name: z.union([z.string(), z.null()]).optional(),
    track_slug: z.union([z.string(), z.null()]).optional(),
    track_name: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const TestCaseInputSchema = z
  .object({
    input_data: z.string(),
    expected_output: z.string(),
    is_hidden: z.boolean().optional().default(true),
  })
  .passthrough();
const ExerciseCreateSchema = z
  .object({
    slug: z.string(),
    title: z.string(),
    statement: z.string(),
    learning_objectives: z.array(z.string()).optional().default([]),
    family_key: z.string().optional().default("code_lab"),
    difficulty: z.string().optional().default("iniciante"),
    language: z.string().optional().default("python"),
    module_slug: z.string().optional().default(""),
    module_name: z.string().optional().default(""),
    module_description: z.string().optional().default(""),
    module_audience: z.string().optional().default(""),
    module_source_kind: z.string().optional().default(""),
    category_slug: z.string().optional().default(""),
    category_name: z.string().optional().default(""),
    track_slug: z.string().optional().default(""),
    track_name: z.string().optional().default(""),
    exercise_type_slug: z.string().optional().default(""),
    estimated_time_minutes: z.number().int().optional().default(15),
    version: z.number().int().optional().default(1),
    content_blocks: z.array(z.object({}).passthrough()).optional().default([]),
    workspace_spec: z.object({}).passthrough().optional().default({}),
    evaluation_plan: z.object({}).passthrough().optional().default({}),
    review_profile: z.string().optional().default("code_lab_default"),
    misconception_tags: z.array(z.string()).optional().default([]),
    progression_rules: z.object({}).passthrough().optional().default({}),
    track_position: z.number().int().optional().default(0),
    concept_summary: z.string().optional().default(""),
    pedagogical_brief: z.string().optional().default(""),
    starter_code: z.string().optional().default(""),
    sample_input: z.string().optional().default(""),
    sample_output: z.string().optional().default(""),
    professor_note: z.string().optional().default(""),
    test_cases: z.array(TestCaseInputSchema),
  })
  .passthrough();
const ExerciseTestCaseSchema = z
  .object({
    id: z.number().int(),
    input_data: z.string(),
    expected_output: z.string(),
    is_hidden: z.boolean(),
  })
  .passthrough();
const ExerciseDetailSchema = z
  .object({
    id: z.number().int(),
    slug: z.string(),
    title: z.string(),
    learning_objectives: z.array(z.string()).optional().default([]),
    family_key: z.string().optional().default("code_lab"),
    difficulty: z.string(),
    language: z.string(),
    professor_note: z.string(),
    exercise_type: z.string().optional().default("drill-de-implementacao"),
    exercise_type_label: z
      .string()
      .optional()
      .default("Drill de implementação"),
    estimated_time_minutes: z.number().int().optional().default(15),
    concept_summary: z.string().optional().default(""),
    track_position: z.number().int().optional().default(0),
    module_slug: z.union([z.string(), z.null()]).optional(),
    module_name: z.union([z.string(), z.null()]).optional(),
    category_slug: z.union([z.string(), z.null()]).optional(),
    category_name: z.union([z.string(), z.null()]).optional(),
    track_slug: z.union([z.string(), z.null()]).optional(),
    track_name: z.union([z.string(), z.null()]).optional(),
    statement: z.string(),
    version: z.number().int().optional().default(1),
    content_blocks: z.array(z.object({}).passthrough()).optional().default([]),
    workspace_spec: z.object({}).passthrough().optional().default({}),
    evaluation_plan: z.object({}).passthrough().optional().default({}),
    review_profile: z.string().optional().default("code_lab_default"),
    misconception_tags: z.array(z.string()).optional().default([]),
    progression_rules: z.object({}).passthrough().optional().default({}),
    starter_code: z.string(),
    sample_input: z.string(),
    sample_output: z.string(),
    test_cases: z.array(ExerciseTestCaseSchema),
  })
  .passthrough();
const SessionConfigSchema = z
  .object({
    exercise: ExerciseDetailSchema,
    family_key: z.string(),
    surface_key: z.string(),
    mode: z.string(),
    workspace_spec: z.object({}).passthrough(),
    review_profile: z.string(),
  })
  .passthrough();
const SubmissionSnapshotSchema = z
  .object({
    id: z.number().int(),
    session_id: z.number().int(),
    type: z.string(),
    payload: z.object({}).passthrough(),
    files: z.object({}).passthrough(),
    selected_options: z.array(z.string()),
    created_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const EvaluationRunSchema = z
  .object({
    id: z.number().int(),
    submission_snapshot_id: z.number().int(),
    normalized_score: z.number(),
    verdict: z.string(),
    evaluator_results: z.object({}).passthrough(),
    evidence_bundle: z.object({}).passthrough(),
    misconception_inference: z.array(z.string()),
    raw_artifacts: z.object({}).passthrough(),
    created_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const AIReviewSchema = z
  .object({
    id: z.number().int(),
    evaluation_run_id: z.number().int(),
    profile_key: z.string(),
    explanation: z.string(),
    next_steps: z.array(z.string()),
    conversation_thread: z.array(z.object({}).passthrough()),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const ProgressRewardSchema = z
  .object({
    milestone_key: z.string(),
    label: z.string(),
    xp_awarded: z.number().int(),
  })
  .passthrough();
const ExerciseProgressSchema = z
  .object({
    attempts_count: z.number().int(),
    best_passed_tests: z.number().int(),
    best_total_tests: z.number().int(),
    best_ratio: z.number(),
    xp_awarded_total: z.number().int(),
    first_passed_at: z.union([z.string(), z.null()]).optional(),
    awarded_progress_markers: z.array(z.string()),
  })
  .passthrough();
const UserProgressSummarySchema = z
  .object({
    xp_total: z.number().int(),
    level: z.number().int(),
    xp_into_level: z.number().int(),
    xp_to_next_level: z.number().int(),
  })
  .passthrough();
const AttemptSessionSchema = z
  .object({
    id: z.number().int(),
    target_type: z.string(),
    exercise_slug: z.union([z.string(), z.null()]).optional(),
    exercise_title: z.union([z.string(), z.null()]).optional(),
    assessment_slug: z.union([z.string(), z.null()]).optional(),
    assessment_title: z.union([z.string(), z.null()]).optional(),
    family_key: z.union([z.string(), z.null()]).optional(),
    surface_key: z.union([z.string(), z.null()]).optional(),
    mode: z.string(),
    state: z.object({}).passthrough(),
    current_workspace_state: z.object({}).passthrough(),
    answer_state: z.object({}).passthrough(),
    attempt_status: z.string(),
    latest_snapshot: z.union([SubmissionSnapshotSchema, z.null()]).optional(),
    latest_evaluation: z.union([EvaluationRunSchema, z.null()]).optional(),
    latest_review: z.union([AIReviewSchema, z.null()]).optional(),
    xp_awarded: z.number().int().optional().default(0),
    unlocked_progress_rewards: z
      .array(ProgressRewardSchema)
      .optional()
      .default([]),
    exercise_progress: z.union([ExerciseProgressSchema, z.null()]).optional(),
    user_progress: z.union([UserProgressSummarySchema, z.null()]).optional(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const PracticeAnswerInputSchema = z
  .object({
    source_code: z.string().default(""),
    selected_options: z.array(z.string()).default([]),
    response_text: z.string().default(""),
    files: z.object({}).passthrough().default({}),
  })
  .passthrough();
const AttemptEvaluationResponseSchema = z
  .object({
    session: AttemptSessionSchema,
    snapshot: SubmissionSnapshotSchema,
    evaluation: EvaluationRunSchema,
    review: z.union([AIReviewSchema, z.null()]).optional(),
    xp_awarded: z.number().int().optional().default(0),
    unlocked_progress_rewards: z
      .array(ProgressRewardSchema)
      .optional()
      .default([]),
    exercise_progress: z.union([ExerciseProgressSchema, z.null()]).optional(),
    user_progress: z.union([UserProgressSummarySchema, z.null()]).optional(),
  })
  .passthrough();
const AssessmentContainerPartSchema = z
  .object({
    id: z.number().int(),
    title: z.string(),
    sort_order: z.number().int(),
    exercise_slug: z.union([z.string(), z.null()]).optional(),
    scoring_rules: z.object({}).passthrough().optional().default({}),
    timing_rules: z.object({}).passthrough().optional().default({}),
    reveal_rules: z.object({}).passthrough().optional().default({}),
  })
  .passthrough();
const AssessmentContainerSchema = z
  .object({
    id: z.number().int(),
    slug: z.string(),
    title: z.string(),
    mode: z.string(),
    scoring_rules: z.object({}).passthrough().optional().default({}),
    timing_rules: z.object({}).passthrough().optional().default({}),
    reveal_rules: z.object({}).passthrough().optional().default({}),
    parts: z.array(AssessmentContainerPartSchema),
  })
  .passthrough();
const ReviewChatMessageSchema = z
  .object({ role: z.string(), content: z.string() })
  .passthrough();
const ReviewChatInputSchema = z
  .object({
    message: z.string(),
    history: z.array(ReviewChatMessageSchema).optional().default([]),
  })
  .passthrough();
const ReviewChatResponseSchema = z.object({ answer: z.string() }).passthrough();
const TrackSummarySchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    module_slug: z.union([z.string(), z.null()]).optional(),
    module_name: z.union([z.string(), z.null()]).optional(),
    category_slug: z.string(),
    category_name: z.string(),
    description: z.string(),
    goal: z.string(),
    level_label: z.string(),
    progress_percent: z.number().int(),
    completed_exercises: z.number().int(),
    total_exercises: z.number().int(),
    current_target_slug: z.union([z.string(), z.null()]).optional(),
    current_target_title: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const NavigatorModuleSchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    description: z.string(),
    audience: z.string(),
    source_kind: z.string(),
    status: z.string(),
    tracks: z.array(TrackSummarySchema),
  })
  .passthrough();
const NavigatorResponseSchema = z
  .object({
    recommended_module_slug: z.union([z.string(), z.null()]).optional(),
    recommended_module_name: z.union([z.string(), z.null()]).optional(),
    recommended_track_slug: z.union([z.string(), z.null()]).optional(),
    recommended_track_name: z.union([z.string(), z.null()]).optional(),
    modules: z.array(NavigatorModuleSchema),
  })
  .passthrough();
const ModuleDetailSchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    description: z.string(),
    audience: z.string(),
    source_kind: z.string(),
    status: z.string(),
    progress_percent: z.number().int(),
    completed_tracks: z.number().int(),
    total_tracks: z.number().int(),
    current_target_track_slug: z.union([z.string(), z.null()]).optional(),
    current_target_track_name: z.union([z.string(), z.null()]).optional(),
    current_target_exercise_slug: z.union([z.string(), z.null()]).optional(),
    current_target_exercise_title: z.union([z.string(), z.null()]).optional(),
    tracks: z.array(TrackSummarySchema),
  })
  .passthrough();
const LearningModuleInputSchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    description: z.string().optional().default(""),
    audience: z.string().optional().default(""),
    source_kind: z.string().optional().default(""),
    status: z.string().optional().default("active"),
    sort_order: z.number().int().optional().default(0),
  })
  .passthrough();
const ExerciseTypeInputSchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    description: z.string().optional().default(""),
    sort_order: z.number().int().optional().default(0),
  })
  .passthrough();
const CatalogAdminReferenceSchema = z
  .object({
    modules: z.array(LearningModuleInputSchema),
    exercise_types: z.array(ExerciseTypeInputSchema),
    categories: z.array(z.object({}).passthrough()),
    tracks: z.array(z.object({}).passthrough()),
  })
  .passthrough();
const TrackConceptInputSchema = z
  .object({
    title: z.string(),
    summary: z.string(),
    why_it_matters: z.string().optional().default(""),
    common_mistake: z.string().optional().default(""),
    sort_order: z.number().int().optional().default(0),
  })
  .passthrough();
const TrackPrerequisiteInputSchema = z
  .object({
    label: z.string(),
    sort_order: z.number().int().optional().default(0),
  })
  .passthrough();
const TrackInputSchema = z
  .object({
    slug: z.string(),
    name: z.string(),
    module_slug: z.string(),
    category_slug: z.string(),
    description: z.string().optional().default(""),
    goal: z.string().optional().default(""),
    level_label: z.string().optional().default(""),
    concept_kicker: z.string().optional().default(""),
    milestone_title: z.string().optional().default(""),
    milestone_summary: z.string().optional().default(""),
    milestone_requirement_label: z.string().optional().default(""),
    sort_order: z.number().int().optional().default(0),
    concepts: z.array(TrackConceptInputSchema).optional().default([]),
    prerequisites: z.array(TrackPrerequisiteInputSchema).optional().default([]),
  })
  .passthrough();
const TrackUpdateSchema = z
  .object({
    name: z.union([z.string(), z.null()]),
    module_slug: z.union([z.string(), z.null()]),
    category_slug: z.union([z.string(), z.null()]),
    description: z.union([z.string(), z.null()]),
    goal: z.union([z.string(), z.null()]),
    level_label: z.union([z.string(), z.null()]),
    concept_kicker: z.union([z.string(), z.null()]),
    milestone_title: z.union([z.string(), z.null()]),
    milestone_summary: z.union([z.string(), z.null()]),
    milestone_requirement_label: z.union([z.string(), z.null()]),
    sort_order: z.union([z.number(), z.null()]),
    concepts: z.union([z.array(TrackConceptInputSchema), z.null()]),
    prerequisites: z.union([z.array(TrackPrerequisiteInputSchema), z.null()]),
  })
  .passthrough();
const ExerciseCatalogUpdateSchema = z
  .object({
    track_slug: z.union([z.string(), z.null()]),
    exercise_type_slug: z.union([z.string(), z.null()]),
    estimated_time_minutes: z.union([z.number(), z.null()]),
    track_position: z.union([z.number(), z.null()]),
    concept_summary: z.union([z.string(), z.null()]),
    pedagogical_brief: z.union([z.string(), z.null()]),
  })
  .passthrough();

export const schemas = {
  authorization,
  TrackConceptSchema,
  TrackExerciseProgressSchema,
  TrackExerciseSchema,
  TrackMilestoneSchema,
  TrackDetailSchema,
  ErrorSchema,
  ExplanationConceptSchema,
  ExplanationCodeExampleSchema,
  ExerciseExplanationSchema,
  LoginInputSchema,
  UserSchema,
  LoginResponseSchema,
  ExerciseSummarySchema,
  TestCaseInputSchema,
  ExerciseCreateSchema,
  ExerciseTestCaseSchema,
  ExerciseDetailSchema,
  SessionConfigSchema,
  SubmissionSnapshotSchema,
  EvaluationRunSchema,
  AIReviewSchema,
  ProgressRewardSchema,
  ExerciseProgressSchema,
  UserProgressSummarySchema,
  AttemptSessionSchema,
  PracticeAnswerInputSchema,
  AttemptEvaluationResponseSchema,
  AssessmentContainerPartSchema,
  AssessmentContainerSchema,
  ReviewChatMessageSchema,
  ReviewChatInputSchema,
  ReviewChatResponseSchema,
  TrackSummarySchema,
  NavigatorModuleSchema,
  NavigatorResponseSchema,
  ModuleDetailSchema,
  LearningModuleInputSchema,
  ExerciseTypeInputSchema,
  CatalogAdminReferenceSchema,
  TrackConceptInputSchema,
  TrackPrerequisiteInputSchema,
  TrackInputSchema,
  TrackUpdateSchema,
  ExerciseCatalogUpdateSchema,
};

export const catalogEndpoints = makeApi([
  {
    method: "get",
    path: "/api/catalog/tracks/:track_slug",
    alias: "apps_catalog_interface_api_get_track_detail",
    requestFormat: "json",
    parameters: [
      {
        name: "track_slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: TrackDetailSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/catalog/tracks/:track_slug/explanations/:exercise_slug",
    alias: "apps_catalog_interface_api_get_track_explanation",
    requestFormat: "json",
    parameters: [
      {
        name: "track_slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "exercise_slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: ExerciseExplanationSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/catalog/navigator",
    alias: "apps_catalog_interface_api_get_navigator",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: NavigatorResponseSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/catalog/modules/:module_slug",
    alias: "apps_catalog_interface_api_get_module_detail",
    requestFormat: "json",
    parameters: [
      {
        name: "module_slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: ModuleDetailSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const catalogApi = new Zodios(catalogEndpoints);

export const authEndpoints = makeApi([
  {
    method: "post",
    path: "/api/auth/login",
    alias: "apps_accounts_interface_api_login",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LoginInputSchema,
      },
    ],
    response: LoginResponseSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/auth/me",
    alias: "apps_accounts_interface_api_me",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: UserSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const authApi = new Zodios(authEndpoints);

export const practiceEndpoints = makeApi([
  {
    method: "get",
    path: "/api/practice/exercises",
    alias: "apps_practice_interface_api_list_exercises",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.array(ExerciseSummarySchema),
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/practice/exercises",
    alias: "apps_practice_interface_api_post_exercise",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ExerciseCreateSchema,
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: ExerciseDetailSchema,
    errors: [
      {
        status: 400,
        description: `Bad Request`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/practice/exercises/:slug",
    alias: "apps_practice_interface_api_get_exercise",
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: ExerciseDetailSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/practice/exercises/:slug/session-config",
    alias: "apps_practice_interface_api_get_exercise_session_config",
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: SessionConfigSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/practice/exercises/:slug/sessions",
    alias: "apps_practice_interface_api_create_exercise_session",
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptSessionSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/practice/sessions",
    alias: "apps_practice_interface_api_list_practice_sessions",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.array(AttemptSessionSchema),
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/practice/sessions/:session_id",
    alias: "apps_practice_interface_api_get_practice_session",
    requestFormat: "json",
    parameters: [
      {
        name: "session_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptSessionSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "patch",
    path: "/api/practice/sessions/:session_id",
    alias: "apps_practice_interface_api_patch_practice_session",
    requestFormat: "json",
    parameters: [
      {
        name: "session_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "payload",
        type: "Query",
        schema: z.object({}).passthrough(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptSessionSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/practice/sessions/:session_id/run",
    alias: "apps_practice_interface_api_run_practice_session",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PracticeAnswerInputSchema,
      },
      {
        name: "session_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptEvaluationResponseSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/practice/sessions/:session_id/check",
    alias: "apps_practice_interface_api_check_practice_session",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PracticeAnswerInputSchema,
      },
      {
        name: "session_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptEvaluationResponseSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/practice/sessions/:session_id/submit",
    alias: "apps_practice_interface_api_submit_practice_session",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PracticeAnswerInputSchema,
      },
      {
        name: "session_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptEvaluationResponseSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const practiceApi = new Zodios(practiceEndpoints);

export const assessmentsEndpoints = makeApi([
  {
    method: "get",
    path: "/api/assessments/:slug",
    alias: "apps_practice_interface_api_get_assessment",
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AssessmentContainerSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/assessments/:slug/sessions",
    alias: "apps_practice_interface_api_create_assessment_session",
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AttemptSessionSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const assessmentsApi = new Zodios(assessmentsEndpoints);

export const reviewEndpoints = makeApi([
  {
    method: "get",
    path: "/api/review/evaluations/:evaluation_run_id",
    alias: "apps_review_interface_api_get_evaluation",
    requestFormat: "json",
    parameters: [
      {
        name: "evaluation_run_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: EvaluationRunSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/review/evaluations/:evaluation_run_id/review",
    alias: "apps_review_interface_api_get_evaluation_review",
    requestFormat: "json",
    parameters: [
      {
        name: "evaluation_run_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: AIReviewSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/review/evaluations/:evaluation_run_id/chat",
    alias: "apps_review_interface_api_review_evaluation_chat",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReviewChatInputSchema,
      },
      {
        name: "evaluation_run_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.object({ answer: z.string() }).passthrough(),
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const reviewApi = new Zodios(reviewEndpoints);

export const progressEndpoints = makeApi([
  {
    method: "get",
    path: "/api/progress/me",
    alias: "apps_progress_interface_api_get_my_progress",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: UserProgressSummarySchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const progressApi = new Zodios(progressEndpoints);

export const catalog_adminEndpoints = makeApi([
  {
    method: "get",
    path: "/api/catalog-admin/reference",
    alias: "apps_catalog_interface_api_get_catalog_reference",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: CatalogAdminReferenceSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/catalog-admin/modules",
    alias: "apps_catalog_interface_api_list_modules",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.array(LearningModuleInputSchema),
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/catalog-admin/modules",
    alias: "apps_catalog_interface_api_upsert_module",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LearningModuleInputSchema,
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: LearningModuleInputSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/catalog-admin/exercise-types",
    alias: "apps_catalog_interface_api_list_exercise_types",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.array(ExerciseTypeInputSchema),
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/catalog-admin/exercise-types",
    alias: "apps_catalog_interface_api_upsert_exercise_type",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ExerciseTypeInputSchema,
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: ExerciseTypeInputSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/catalog-admin/tracks",
    alias: "apps_catalog_interface_api_list_tracks",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.array(TrackDetailSchema),
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/catalog-admin/tracks",
    alias: "apps_catalog_interface_api_create_track",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TrackInputSchema,
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: TrackDetailSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "patch",
    path: "/api/catalog-admin/tracks/:track_slug",
    alias: "apps_catalog_interface_api_update_track",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TrackUpdateSchema,
      },
      {
        name: "track_slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: TrackDetailSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "patch",
    path: "/api/catalog-admin/exercises/:slug/catalog",
    alias: "apps_catalog_interface_api_update_exercise_catalog",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ExerciseCatalogUpdateSchema,
      },
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: ExerciseDetailSchema,
    errors: [
      {
        status: 401,
        description: `Unauthorized`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
      {
        status: 404,
        description: `Not Found`,
        schema: z.object({ message: z.string() }).passthrough(),
      },
    ],
  },
]);

export const catalog_adminApi = new Zodios(catalog_adminEndpoints);

export const systemEndpoints = makeApi([
  {
    method: "get",
    path: "/api/health",
    alias: "apps_arena_api_health",
    requestFormat: "json",
    response: z.void(),
  },
]);

export const systemApi = new Zodios(systemEndpoints);

