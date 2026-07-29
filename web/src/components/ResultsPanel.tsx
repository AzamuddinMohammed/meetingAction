import type { ActionItem, ExportResponse, MeetingAnalysis } from "../types";
import { ActionItemsTable } from "./ActionItemsTable";
import { CopyButton } from "./CopyButton";

interface Props {
  analysis: MeetingAnalysis;
  actionItems: ActionItem[];
  onActionItemsChange: (items: ActionItem[]) => void;
  jiraAvailable: boolean;
  notionAvailable: boolean;
  onExport: (target: "jira" | "notion") => void;
  exporting: "jira" | "notion" | null;
  exportResult: ExportResponse | null;
}

export function ResultsPanel(props: Props) {
  const { analysis } = props;
  const emailText = `Subject: ${analysis.follow_up_email.subject}\n\n${analysis.follow_up_email.body}`;

  return (
    <section className="panel results-panel" aria-label="Analysis results">
      <div className="result-block">
        <h2>Summary</h2>
        <p className="summary-text">{analysis.summary}</p>
      </div>

      {analysis.key_points.length > 0 && (
        <div className="result-block">
          <h2>Key points</h2>
          <ul className="bullet-list">
            {analysis.key_points.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.decisions.length > 0 && (
        <div className="result-block">
          <h2>Decisions</h2>
          <ul className="decision-list">
            {analysis.decisions.map((d, i) => (
              <li key={i}>
                <strong>{d.decision}</strong>
                {d.rationale && <span className="rationale"> — {d.rationale}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="result-block">
        <div className="block-header">
          <h2>Action items</h2>
          <div className="export-actions">
            {props.jiraAvailable && (
              <button
                className="btn ghost small"
                onClick={() => props.onExport("jira")}
                disabled={props.exporting !== null || props.actionItems.length === 0}
              >
                {props.exporting === "jira" ? "Exporting…" : "Export to Jira"}
              </button>
            )}
            {props.notionAvailable && (
              <button
                className="btn ghost small"
                onClick={() => props.onExport("notion")}
                disabled={props.exporting !== null || props.actionItems.length === 0}
              >
                {props.exporting === "notion" ? "Exporting…" : "Export to Notion"}
              </button>
            )}
          </div>
        </div>
        <ActionItemsTable
          items={props.actionItems}
          onChange={props.onActionItemsChange}
        />
        {props.exportResult && (
          <p className="export-result">
            Created {props.exportResult.created.length} item(s) in{" "}
            {props.exportResult.target}.
            {props.exportResult.created[0]?.url && (
              <>
                {" "}
                <a
                  href={props.exportResult.created[0].url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open first
                </a>
              </>
            )}
          </p>
        )}
      </div>

      {analysis.risks.length > 0 && (
        <div className="result-block">
          <h2>Risks & open questions</h2>
          <ul className="bullet-list risk-list">
            {analysis.risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="result-block">
        <div className="block-header">
          <h2>Follow-up email</h2>
          <CopyButton text={emailText} label="Copy email" />
        </div>
        <div className="email-card">
          <div className="email-subject">
            <span className="muted">Subject:</span>{" "}
            {analysis.follow_up_email.subject}
          </div>
          <pre className="email-body">{analysis.follow_up_email.body}</pre>
        </div>
      </div>
    </section>
  );
}
