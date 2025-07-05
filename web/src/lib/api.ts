import { createFetch, createSchema, methods } from "@better-fetch/fetch";
import { z } from "zod";
import {
  ActivitySchema,
  ActivityItemSchema,
  ActivityAnswerCreateSchema,
  AnswerResponseSchema,
  ProfileSchema,
  PatientMetadataSchema,
  FullActivityDetailsSchema,
} from "../schemas/backend";

export const apiSchema = createSchema({
  "/activities/": {
    output: z.array(ActivitySchema),
  },
  "/activities/{activity_id}/details": {
    output: FullActivityDetailsSchema,
  },
  "/activities/{activity_id}/items/{activity_item_id}": {
    output: ActivityItemSchema,
  },
  "@post/activities/create": {
    output: ActivitySchema,
  },
  "/activities/{activity_id}/start": {
    output: ActivityItemSchema,
  },
  "/activities/{activity_id}/items/{activity_item_id}/answer": {
    input: ActivityAnswerCreateSchema,
    output: AnswerResponseSchema,
  },
  "@post/profile/": {
      input: PatientMetadataSchema,
      output: ProfileSchema,
  },
  "@get/profile/": {
      output: ProfileSchema,
  },
});

export const $fetch = createFetch({
  baseURL: `${import.meta.env.VITE_BACKEND_BASE_URL}`,
  throw: true,
  schema: apiSchema,
  headers: {
    Authorization: `Bearer ${import.meta.env.VITE_DUMMY_BUT_VALID_USER_ID}`,
  },
});
