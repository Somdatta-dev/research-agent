import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import {
  useConfig,
  useCreateConfig,
  useDeleteConfig,
  useTestDryRun,
  useUpdateConfig,
} from "../hooks/useReportConfig";
import { Button } from "../components/ui/button";
import { Input, Textarea } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { CronBuilder } from "../components/CronBuilder";
import {
  configFormSchema,
  type ConfigFormValues,
} from "../lib/schema";

const DEFAULTS: ConfigFormValues = {
  name: "",
  topic: "",
  focus_areas: [],
  schedule_cron: "0 7 * * *",
  timezone: "Asia/Kolkata",
  recipients: [],
  search_config: {
    providers: ["tavily", "brave"],
    max_results_per_query: 10,
    recency_days: 2,
  },
  llm_config: { primary: {}, fast: {} },
  dedup_window_days: 7,
  pdf_template: "linkedin_carousel",
  max_pages: 8,
  active: true,
};

export default function ConfigEdit() {
  const { id } = useParams<{ id: string }>();
  const isNew = !id || id === "new";
  const navigate = useNavigate();

  const detail = useConfig(isNew ? undefined : id);
  const create = useCreateConfig();
  const update = useUpdateConfig(id ?? "");
  const softDelete = useDeleteConfig();
  const testRun = useTestDryRun();

  const form = useForm<ConfigFormValues>({
    resolver: zodResolver(configFormSchema),
    defaultValues: DEFAULTS,
  });

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = form;

  const recipientsField = useFieldArray({ control, name: "recipients" });
  const focusField = useFieldArray({
    control,
    name: "focus_areas" as never,
  });

  useEffect(() => {
    if (!isNew && detail.data) {
      reset({
        name: detail.data.name,
        topic: detail.data.topic,
        focus_areas: detail.data.focus_areas,
        schedule_cron: detail.data.schedule_cron,
        timezone: detail.data.timezone,
        recipients: detail.data.recipients,
        search_config: detail.data.search_config,
        llm_config: detail.data.llm_config,
        dedup_window_days: detail.data.dedup_window_days,
        pdf_template: detail.data.pdf_template,
        max_pages: detail.data.max_pages,
        active: detail.data.active,
      });
    }
  }, [isNew, detail.data, reset]);

  const onSubmit = async (values: ConfigFormValues) => {
    if (isNew) {
      const created = await create.mutateAsync(values);
      navigate(`/configs/${created.id}`);
    } else {
      await update.mutateAsync(values);
    }
  };

  const cron = watch("schedule_cron");
  const tz = watch("timezone");

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="mx-auto max-w-3xl space-y-6"
    >
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            {isNew ? "New config" : "Edit config"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {isNew
              ? "Define the report recipe."
              : `Editing ${detail.data?.name ?? ""}`}
          </p>
        </div>
        <div className="flex gap-2">
          {!isNew && (
            <>
              <Button
                type="button"
                variant="secondary"
                onClick={() => id && testRun.mutate(id)}
                disabled={testRun.isPending}
              >
                Test dry-run
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  if (
                    id &&
                    window.confirm("Deactivate this config? It won't run on schedule.")
                  ) {
                    softDelete.mutate(id, { onSuccess: () => navigate("/configs") });
                  }
                }}
                disabled={softDelete.isPending}
              >
                <Trash2 className="h-3.5 w-3.5" /> Deactivate
              </Button>
            </>
          )}
          <Button type="submit" disabled={isSubmitting}>
            {isNew ? "Create" : "Save"}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Basics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="name">Name</Label>
            <Input id="name" {...register("name")} />
            {errors.name && (
              <p className="mt-1 text-xs text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="topic">Topic</Label>
            <Textarea
              id="topic"
              rows={3}
              {...register("topic")}
              placeholder="AI implementations across Automobile / Manufacturing"
            />
            {errors.topic && (
              <p className="mt-1 text-xs text-destructive">
                {errors.topic.message}
              </p>
            )}
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <Label>Focus areas</Label>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => focusField.append("" as never)}
              >
                <Plus className="h-3.5 w-3.5" /> Add
              </Button>
            </div>
            <div className="space-y-2">
              {focusField.fields.map((f, idx) => (
                <div key={f.id} className="flex gap-2">
                  <Input
                    {...register(`focus_areas.${idx}` as const)}
                    placeholder="e.g. OEMs, Tier-1 suppliers, factory automation"
                  />
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    onClick={() => focusField.remove(idx)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
              {focusField.fields.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  No focus areas — the agent will use the topic as-is.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <CronBuilder
            cron={cron}
            timezone={tz}
            onCronChange={(v) => setValue("schedule_cron", v)}
            onTimezoneChange={(v) => setValue("timezone", v)}
            error={errors.schedule_cron?.message}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recipients</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {recipientsField.fields.map((f, idx) => (
              <div key={f.id} className="grid grid-cols-[1fr_1fr_auto] gap-2">
                <Input
                  {...register(`recipients.${idx}.email` as const)}
                  placeholder="person@domain.com"
                  type="email"
                />
                <Input
                  {...register(`recipients.${idx}.name` as const)}
                  placeholder="Display name (optional)"
                />
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={() => recipientsField.remove(idx)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() =>
                recipientsField.append({ email: "", name: "" })
              }
            >
              <Plus className="h-3.5 w-3.5" /> Add recipient
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-4">
          <div>
            <Label htmlFor="max_results_per_query">Results / query</Label>
            <Input
              id="max_results_per_query"
              type="number"
              {...register("search_config.max_results_per_query", {
                valueAsNumber: true,
              })}
            />
          </div>
          <div>
            <Label htmlFor="recency_days">Recency (days)</Label>
            <Input
              id="recency_days"
              type="number"
              {...register("search_config.recency_days", {
                valueAsNumber: true,
              })}
            />
          </div>
          <div>
            <Label htmlFor="dedup_window_days">Dedup window (days)</Label>
            <Input
              id="dedup_window_days"
              type="number"
              {...register("dedup_window_days", { valueAsNumber: true })}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>LLM (per-report overrides)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <p className="text-xs text-muted-foreground">
            All fields optional. Leave blank to use environment defaults. Set
            model / base_url / api_key to switch providers for this config only.
          </p>

          {(["primary", "fast"] as const).map((tier) => (
            <div key={tier} className="rounded-lg border border-border p-4">
              <div className="mb-3 text-sm font-semibold capitalize">
                {tier}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Model</Label>
                  <Input
                    {...register(`llm_config.${tier}.model` as const)}
                    placeholder="e.g. openai/gpt-4o"
                  />
                </div>
                <div>
                  <Label>Base URL</Label>
                  <Input
                    {...register(`llm_config.${tier}.base_url` as const)}
                    placeholder="https://openrouter.ai/api/v1"
                  />
                </div>
                <div>
                  <Label>API key</Label>
                  <Input
                    {...register(`llm_config.${tier}.api_key` as const)}
                    type="password"
                    placeholder="sk-…"
                    autoComplete="off"
                  />
                </div>
                <div>
                  <Label>Temperature</Label>
                  <Input
                    {...register(`llm_config.${tier}.temperature` as const, {
                      valueAsNumber: true,
                    })}
                    type="number"
                    step="0.1"
                    placeholder="0.3"
                  />
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Output</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-4">
          <div>
            <Label htmlFor="max_pages">Max pages</Label>
            <Input
              id="max_pages"
              type="number"
              {...register("max_pages", { valueAsNumber: true })}
            />
          </div>
          <div>
            <Label htmlFor="pdf_template">PDF template</Label>
            <Input id="pdf_template" {...register("pdf_template")} />
          </div>
          <div className="flex items-end gap-2">
            <input
              id="active"
              type="checkbox"
              {...register("active")}
              className="h-4 w-4 accent-primary"
            />
            <Label htmlFor="active">Active</Label>
          </div>
        </CardContent>
      </Card>
    </form>
  );
}
