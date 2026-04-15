export type {
  AttemptEvaluationResponse,
  AttemptSession,
  ExerciseProgress,
  PracticeEvaluationResponse,
  PracticeSession,
  ProgressReward,
  SessionConfig,
  SubmissionSnapshot,
  UserProgressSummary,
} from '@/entities/practice-session'
export type { ReviewChatMessage } from '@/entities/review'
import type {
  ExerciseProgress as CanonicalExerciseProgress,
  ProgressReward as CanonicalProgressReward,
  UserProgressSummary as CanonicalUserProgressSummary,
} from '@/entities/practice-session'
import type { ReviewChatMessage as CanonicalReviewChatMessage } from '@/entities/review'

export type FeedbackPayload = {
  summary: string
  strengths: string[]
  issues: string[]
  next_steps: string[]
  source: string
}

export type SubmissionResult = {
  index: number
  input_data: string
  expected_output: string
  actual_output: string
  passed: boolean
  stderr: string
}

export type SubmissionSummary = {
  id: number
  exercise_slug: string
  exercise_title: string
  status: string
  passed_tests: number
  total_tests: number
  feedback_status: string
  feedback_source: string
  created_at: string
  evaluation_run_id: number | null
}

export type Submission = {
  id: number
  session_id: number
  evaluation_run_id: number | null
  exercise_slug: string | null
  exercise_title: string | null
  status: string
  passed_tests: number
  total_tests: number
  source_code: string
  console_output: string
  feedback: string
  feedback_status: string
  feedback_source: string
  feedback_payload: FeedbackPayload | null
  review_chat_history: CanonicalReviewChatMessage[]
  created_at: string
  results: SubmissionResult[]
  xp_awarded: number
  unlocked_progress_rewards: CanonicalProgressReward[]
  exercise_progress: CanonicalExerciseProgress | null
  user_progress: CanonicalUserProgressSummary | null
}
