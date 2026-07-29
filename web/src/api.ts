// Thin, typed client for the MeetingAction API. All paths are relative to the
// current origin (/api/...), which works both behind the Vite dev proxy and on
// Vercel where the Python function serves /api.

import type {
  ActionItem,
  AnalyzeResponse,
  ExportResponse,
  HealthResponse,
} from "./types";

export class ApiRequestError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
  }
}

async function parseError(res: Response): Promise<ApiRequestError> {
  let code = "http_error";
  let message = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
    } else if (body?.detail) {
      // FastAPI validation errors
      message =
        typeof body.detail === "string"
          ? body.detail
          : "The request was invalid.";
      code = "validation_error";
    }
  } catch {
    // non-JSON body; keep defaults
  }
  return new ApiRequestError(message, code, res.status);
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch("/api/health");
  if (!res.ok) throw await parseError(res);
  return res.json();
}

export interface AnalyzeInput {
  transcript: string;
  meeting_title?: string;
  attendees?: string[];
  meeting_date?: string;
}

export async function analyze(input: AnalyzeInput): Promise<AnalyzeResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

export async function transcribe(file: File): Promise<{ transcript: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/transcribe", { method: "POST", body: form });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

export async function exportItems(
  target: "jira" | "notion",
  meetingTitle: string | undefined,
  items: ActionItem[],
): Promise<ExportResponse> {
  const res = await fetch(`/api/export/${target}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      meeting_title: meetingTitle,
      action_items: items.map((i) => ({
        task: i.task,
        owner: i.owner,
        due_date: i.due_date,
        priority: i.priority,
      })),
    }),
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}
