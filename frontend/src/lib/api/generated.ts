import { makeApi, Zodios } from "@zodios/core";
import type { ZodiosOptions } from "@zodios/core";
import { z } from "zod";

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
const ErrorSchema = z.object({ message: z.string() }).passthrough();
const authorization = z.union([z.string(), z.null()]).optional();
const ExerciseSummarySchema = z
  .object({
    id: z.number().int(),
    slug: z.string(),
    title: z.string(),
    difficulty: z.string(),
    language: z.string(),
    professor_note: z.string(),
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
    difficulty: z.string().optional().default("iniciante"),
    language: z.string().optional().default("python"),
    category_slug: z.string().optional().default(""),
    category_name: z.string().optional().default(""),
    track_slug: z.string().optional().default(""),
    track_name: z.string().optional().default(""),
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
    difficulty: z.string(),
    language: z.string(),
    professor_note: z.string(),
    category_slug: z.union([z.string(), z.null()]).optional(),
    category_name: z.union([z.string(), z.null()]).optional(),
    track_slug: z.union([z.string(), z.null()]).optional(),
    track_name: z.union([z.string(), z.null()]).optional(),
    statement: z.string(),
    starter_code: z.string(),
    sample_input: z.string(),
    sample_output: z.string(),
    test_cases: z.array(ExerciseTestCaseSchema),
  })
  .passthrough();
const SubmissionInputSchema = z
  .object({ source_code: z.string() })
  .passthrough();
const FeedbackPayloadSchema = z
  .object({
    summary: z.string(),
    strengths: z.array(z.string()),
    issues: z.array(z.string()),
    next_steps: z.array(z.string()),
    source: z.string(),
  })
  .passthrough();
const ReviewChatMessageSchema = z
  .object({ role: z.string(), content: z.string() })
  .passthrough();
const TestResultSchema = z
  .object({
    index: z.number().int(),
    input_data: z.string(),
    expected_output: z.string(),
    actual_output: z.string(),
    passed: z.boolean(),
    stderr: z.string(),
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
const SubmissionSchema = z
  .object({
    id: z.number().int(),
    status: z.string(),
    passed_tests: z.number().int(),
    total_tests: z.number().int(),
    source_code: z.string(),
    console_output: z.string(),
    feedback: z.string(),
    feedback_status: z.string(),
    feedback_source: z.string(),
    feedback_payload: FeedbackPayloadSchema,
    review_chat_history: z.array(ReviewChatMessageSchema),
    created_at: z.string().datetime({ offset: true }),
    results: z.array(TestResultSchema),
    xp_awarded: z.number().int(),
    unlocked_progress_rewards: z.array(ProgressRewardSchema),
    exercise_progress: ExerciseProgressSchema,
    user_progress: UserProgressSummarySchema,
  })
  .passthrough();
const SubmissionSummarySchema = z
  .object({
    id: z.number().int(),
    exercise_slug: z.string(),
    exercise_title: z.string(),
    status: z.string(),
    passed_tests: z.number().int(),
    total_tests: z.number().int(),
    feedback_status: z.string(),
    feedback_source: z.string(),
    created_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const ReviewChatInputSchema = z
  .object({
    message: z.string(),
    history: z.array(ReviewChatMessageSchema).optional().default([]),
  })
  .passthrough();
const ReviewChatResponseSchema = z.object({ answer: z.string() }).passthrough();

export const schemas = {
  LoginInputSchema,
  UserSchema,
  LoginResponseSchema,
  ErrorSchema,
  authorization,
  ExerciseSummarySchema,
  TestCaseInputSchema,
  ExerciseCreateSchema,
  ExerciseTestCaseSchema,
  ExerciseDetailSchema,
  SubmissionInputSchema,
  FeedbackPayloadSchema,
  ReviewChatMessageSchema,
  TestResultSchema,
  ProgressRewardSchema,
  ExerciseProgressSchema,
  UserProgressSummarySchema,
  SubmissionSchema,
  SubmissionSummarySchema,
  ReviewChatInputSchema,
  ReviewChatResponseSchema,
};

export const authEndpoints = makeApi([
  {
    method: "post",
    path: "/api/auth/login",
    alias: "arena_api_login",
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
    alias: "arena_api_me",
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

export const exercisesEndpoints = makeApi([
  {
    method: "get",
    path: "/api/exercises/",
    alias: "arena_api_list_exercises",
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
    path: "/api/exercises/",
    alias: "arena_api_post_exercise",
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
    path: "/api/exercises/:slug",
    alias: "arena_api_get_exercise",
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
    ],
  },
]);

export const exercisesApi = new Zodios(exercisesEndpoints);

export const submissionsEndpoints = makeApi([
  {
    method: "post",
    path: "/api/submissions/exercises/:slug/submit",
    alias: "arena_api_submit_exercise",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ source_code: z.string() }).passthrough(),
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
    response: SubmissionSchema,
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
    path: "/api/submissions/me",
    alias: "arena_api_list_my_submissions",
    requestFormat: "json",
    parameters: [
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: z.array(SubmissionSummarySchema),
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
    path: "/api/submissions/:submission_id",
    alias: "arena_api_get_submission",
    requestFormat: "json",
    parameters: [
      {
        name: "submission_id",
        type: "Path",
        schema: z.number().int(),
      },
      {
        name: "authorization",
        type: "Header",
        schema: authorization,
      },
    ],
    response: SubmissionSchema,
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
    path: "/api/submissions/:submission_id/review-chat",
    alias: "arena_api_review_chat",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReviewChatInputSchema,
      },
      {
        name: "submission_id",
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

export const submissionsApi = new Zodios(submissionsEndpoints);

export const systemEndpoints = makeApi([
  {
    method: "get",
    path: "/api/health",
    alias: "arena_api_health",
    requestFormat: "json",
    response: z.void(),
  },
]);

export const systemApi = new Zodios(systemEndpoints);

export const endpoints = makeApi([
  ...authEndpoints,
  ...exercisesEndpoints,
  ...submissionsEndpoints,
  ...systemEndpoints,
]);

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options);
}
