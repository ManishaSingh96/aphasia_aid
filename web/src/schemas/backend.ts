import { z } from "zod";

export const ActivityStatusSchema = z.enum(["IDLE", "ONGOING", "COMPLETED"]);
export const ActivityItemStatusSchema = z.enum(["NOT_TERMINATED", "RETRIES_EXHAUST", "SKIP", "SUCCESS"]);
export const ActivityItemTypeSchema = z.enum(["FREE_TEXT"]);

export const FreeTextAnswerHintSchema = z.object({
  activity_type: z.literal("FREE_TEXT"),
});

export const FreeTextAnswerSchema = z.object({
  activity_type: z.literal("FREE_TEXT"),
  text: z.string(),
});

export const FreeTextQuestionConfigSchema = z.object({
  order: z.number().default(0),
  hints: z.array(FreeTextAnswerHintSchema).default([]),
  activity_type: z.literal("FREE_TEXT"),
  prompt: z.string(),
});

export const FreeTextQuestionEvaluationConfigSchema = z.object({
  activity_type: z.literal("FREE_TEXT"),
  expected_answer: z.string(),
});

export const ActivityAnswerSchema = z.object({
  activity_item_id: z.string().uuid(),
  skip: z.boolean().default(false),
  is_correct: z.boolean().default(false),
  answer: z.discriminatedUnion("activity_type", [FreeTextAnswerSchema]),
  id: z.string().uuid(),
  attempted_at: z.string().datetime(),
});

export const ActivitySchema = z.object({
  user_id: z.string().uuid(),
  status: ActivityStatusSchema.default("IDLE"),
  generated_title: z.string().nullable(),
  id: z.string().uuid(),
  created_at: z.string().datetime(),
});

export const FullActivityDetailsSchema = z.object({
  activity: ActivitySchema,
  activity_items: z.array(z.lazy(() => ActivityItemSchema)),
  activity_answers: z.array(z.lazy(() => ActivityAnswerSchema)),
});

export const ActivityItemSchema = z.object({
  activity_type: ActivityItemTypeSchema,
  activity_id: z.string().uuid(),
  max_retries: z.number().default(2),
  attempted_retries: z.number().default(0),
  status: ActivityItemStatusSchema.default("NOT_TERMINATED"),
  id: z.string().uuid(),
  created_at: z.string().datetime(),
  question_config: z.discriminatedUnion("activity_type", [FreeTextQuestionConfigSchema]),
  question_evaluation_config: z.discriminatedUnion("activity_type", [FreeTextQuestionEvaluationConfigSchema]),
});

export const ActivityAnswerCreateSchema = z.object({
  activity_item_id: z.string().uuid(),
  skip: z.boolean().default(false),
  is_correct: z.boolean().default(false),
  answer: z.discriminatedUnion("activity_type", [FreeTextAnswerSchema]),
});

export const AnswerResponseSchema = z.object({
  activity_type: ActivityItemTypeSchema,
  next_item_id: z.string().nullable(),
  success_verdict: z.boolean(),
  activity_complete: z.boolean(),
  hints: z.array(z.discriminatedUnion("activity_type", [FreeTextAnswerHintSchema])).default([]),
});

export const PatientMetadataSchema = z.object({
  patient_name: z.string(),
  patient_age: z.number(),
  city: z.string(),
  language: z.string(),
  diagnosis: z.string(),
  patient_address: z.string().nullable(),
  state: z.string().nullable(),
  country: z.string().nullable(),
  profession: z.string().nullable(),
  education: z.string().nullable(),
});

export const ProfileSchema = z.object({
  user_id: z.string().uuid(),
  metadata: PatientMetadataSchema,
});
