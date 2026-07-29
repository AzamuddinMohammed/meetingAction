// Mirrors the backend Pydantic schemas (server/schemas.py).

export type Priority = "low" | "medium" | "high";
export type ActionStatus = "open" | "in_progress" | "done";

export interface ActionItem {
  id: string;
  task: string;
  owner: string | null;
  due_date: string | null;
  priority: Priority;
  status: ActionStatus;
}

export interface Decision {
  decision: string;
  rationale: string | null;
}

export interface Email {
  subject: string;
  body: string;
}

export interface MeetingAnalysis {
  summary: string;
  key_points: string[];
  decisions: Decision[];
  action_items: ActionItem[];
  risks: string[];
  follow_up_email: Email;
}

export interface AnalyzeResponse {
  analysis: MeetingAnalysis;
  model: string;
  usage: Record<string, number>;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  features: {
    analysis: boolean;
    transcription: boolean;
    jira_export: boolean;
    notion_export: boolean;
  };
}

export interface ExportedRecord {
  task: string;
  external_id: string;
  url: string | null;
}

export interface ExportResponse {
  target: "jira" | "notion";
  created: ExportedRecord[];
}

export interface ApiError {
  code: string;
  message: string;
}
