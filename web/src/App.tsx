import { useEffect, useState } from "react";
import {
  ApiRequestError,
  analyze,
  exportItems,
  getHealth,
  transcribe,
} from "./api";
import { InputPanel } from "./components/InputPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import type {
  ActionItem,
  ExportResponse,
  HealthResponse,
  MeetingAnalysis,
} from "./types";

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const [transcript, setTranscript] = useState("");
  const [meetingTitle, setMeetingTitle] = useState("");
  const [attendees, setAttendees] = useState("");
  const [meetingDate, setMeetingDate] = useState("");

  const [analysis, setAnalysis] = useState<MeetingAnalysis | null>(null);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [usageModel, setUsageModel] = useState<string>("");

  const [analyzing, setAnalyzing] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [exporting, setExporting] = useState<"jira" | "notion" | null>(null);
  const [exportResult, setExportResult] = useState<ExportResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function onAnalyze() {
    setError(null);
    setExportResult(null);
    setAnalyzing(true);
    try {
      const res = await analyze({
        transcript,
        meeting_title: meetingTitle || undefined,
        attendees: attendees
          .split(",")
          .map((a) => a.trim())
          .filter(Boolean),
        meeting_date: meetingDate || undefined,
      });
      setAnalysis(res.analysis);
      setActionItems(res.analysis.action_items);
      setUsageModel(res.model);
    } catch (e) {
      setAnalysis(null);
      setError(messageFor(e));
    } finally {
      setAnalyzing(false);
    }
  }

  async function onTranscribe(file: File) {
    setError(null);
    setTranscribing(true);
    try {
      const res = await transcribe(file);
      setTranscript((prev) => (prev ? `${prev}\n${res.transcript}` : res.transcript));
    } catch (e) {
      setError(messageFor(e));
    } finally {
      setTranscribing(false);
    }
  }

  async function onExport(target: "jira" | "notion") {
    setError(null);
    setExportResult(null);
    setExporting(target);
    try {
      const res = await exportItems(target, meetingTitle || undefined, actionItems);
      setExportResult(res);
    } catch (e) {
      setError(messageFor(e));
    } finally {
      setExporting(null);
    }
  }

  const features = health?.features;

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="logo" aria-hidden="true">
            ◆
          </span>
          <div>
            <h1>MeetingAction</h1>
            <p className="tagline">Transcript → summary, decisions & action items</p>
          </div>
        </div>
        <div className="status">
          {health ? (
            <span className="status-ok" title={`API v${health.version}`}>
              API online
            </span>
          ) : (
            <span className="status-off">API unreachable</span>
          )}
        </div>
      </header>

      {health && !features?.analysis && (
        <div className="banner warning">
          The analysis service is not configured. Set <code>ANTHROPIC_API_KEY</code>{" "}
          on the server to enable it.
        </div>
      )}

      {error && (
        <div className="banner error" role="alert">
          {error}
        </div>
      )}

      <main className="layout">
        <InputPanel
          transcript={transcript}
          setTranscript={setTranscript}
          meetingTitle={meetingTitle}
          setMeetingTitle={setMeetingTitle}
          attendees={attendees}
          setAttendees={setAttendees}
          meetingDate={meetingDate}
          setMeetingDate={setMeetingDate}
          transcriptionAvailable={!!features?.transcription}
          onAnalyze={onAnalyze}
          onTranscribe={onTranscribe}
          analyzing={analyzing}
          transcribing={transcribing}
        />

        {analysis ? (
          <ResultsPanel
            analysis={analysis}
            actionItems={actionItems}
            onActionItemsChange={setActionItems}
            jiraAvailable={!!features?.jira_export}
            notionAvailable={!!features?.notion_export}
            onExport={onExport}
            exporting={exporting}
            exportResult={exportResult}
          />
        ) : (
          <section className="panel placeholder">
            <div className="placeholder-inner">
              <p className="placeholder-title">No analysis yet</p>
              <p className="placeholder-sub">
                Paste a transcript and click <strong>Analyze meeting</strong> to
                extract a summary, decisions, and owned action items.
              </p>
            </div>
          </section>
        )}
      </main>

      <footer className="app-footer">
        {usageModel && <span>Analyzed with {usageModel}. </span>}
        <span>MeetingAction — FDE mini-project.</span>
      </footer>
    </div>
  );
}

function messageFor(e: unknown): string {
  if (e instanceof ApiRequestError) return e.message;
  if (e instanceof Error) return e.message;
  return "Something went wrong.";
}
