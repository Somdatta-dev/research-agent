import { z } from "zod";

export const recipientSchema = z.object({
  email: z.string().email("valid email required"),
  name: z.string().nullish(),
});

export const llmTierSchema = z.object({
  base_url: z.string().nullish(),
  api_key: z.string().nullish(),
  model: z.string().nullish(),
  temperature: z.number().min(0).max(2).nullish(),
  max_tokens: z.number().int().positive().nullish(),
  timeout_s: z.number().int().positive().nullish(),
});

export const searchConfigSchema = z.object({
  providers: z.array(z.string()).min(1).default(["tavily", "brave"]),
  max_results_per_query: z.number().int().min(1).max(50).default(10),
  recency_days: z.number().int().min(1).max(30).default(2),
});

export const llmConfigSchema = z.object({
  primary: llmTierSchema.default({}),
  fast: llmTierSchema.default({}),
});

export const configFormSchema = z.object({
  name: z.string().min(1, "name required"),
  topic: z.string().min(1, "topic required"),
  focus_areas: z.array(z.string().min(1)).default([]),
  schedule_cron: z
    .string()
    .regex(
      /^\s*\S+\s+\S+\s+\S+\s+\S+\s+\S+\s*$/,
      "must be a 5-field cron expression",
    ),
  timezone: z.string().min(1, "timezone required").default("UTC"),
  recipients: z.array(recipientSchema).default([]),
  search_config: searchConfigSchema.default({
    providers: ["tavily", "brave"],
    max_results_per_query: 10,
    recency_days: 2,
  }),
  llm_config: llmConfigSchema.default({ primary: {}, fast: {} }),
  dedup_window_days: z.number().int().min(1).max(90).default(7),
  pdf_template: z.string().default("linkedin_carousel"),
  max_pages: z.number().int().min(3).max(20).default(8),
  active: z.boolean().default(true),
});

export type ConfigFormValues = z.infer<typeof configFormSchema>;
