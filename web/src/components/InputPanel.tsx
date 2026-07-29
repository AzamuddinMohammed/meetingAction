import { useRef, useState } from "react";

interface Props {
  transcript: string;
  setTranscript: (v: string) => void;
  meetingTitle: string;
  setMeetingTitle: (v: string) => void;
  attendees: string;
  setAttendees: (v: string) => void;
  meetingDate: string;
  setMeetingDate: (v: string) => void;
  transcriptionAvailable: boolean;
  onAnalyze: () => void;
  onTranscribe: (file: File) => void;
  analyzing: boolean;
  transcribing: boolean;
}

const SAMPLE = `Alex: Thanks everyone for joining the Q3 planning sync. First item — the mobile onboarding redesign.
Priya: The new flow tested well. I think we ship it. Blocker is the analytics events aren't wired up.
Alex: Okay, decision: we ship the redesign next Friday. Priya, can you own wiring the analytics events by Wednesday?
Priya: Yes, I'll have them in by Wednesday.
Jordan: One risk — we haven't load-tested the new sign-up service.
Alex: Good call. Jordan, please run a load test before Thursday. High priority.
Jordan: Will do.
Alex: Last thing — legal review of the new terms. Let's punt that to next sprint.`;

export function InputPanel(props: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string>("");

  const canAnalyze = props.transcript.trim().length > 0 && !props.analyzing;

  return (
    <section className="panel input-panel" aria-label="Meeting input">
      <div className="field-grid">
        <label className="field">
          <span>Meeting title</span>
          <input
            type="text"
            placeholder="Q3 planning sync"
            value={props.meetingTitle}
            onChange={(e) => props.setMeetingTitle(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Date</span>
          <input
            type="date"
            value={props.meetingDate}
            onChange={(e) => props.setMeetingDate(e.target.value)}
          />
        </label>
        <label className="field field-wide">
          <span>Attendees (comma-separated)</span>
          <input
            type="text"
            placeholder="Alex, Priya, Jordan"
            value={props.attendees}
            onChange={(e) => props.setAttendees(e.target.value)}
          />
        </label>
      </div>

      <label className="field">
        <span>Transcript or notes</span>
        <textarea
          rows={12}
          placeholder="Paste the meeting transcript or notes here…"
          value={props.transcript}
          onChange={(e) => props.setTranscript(e.target.value)}
        />
      </label>

      <div className="input-actions">
        <button
          className="btn primary"
          onClick={props.onAnalyze}
          disabled={!canAnalyze}
        >
          {props.analyzing ? "Analyzing…" : "Analyze meeting"}
        </button>

        <button
          className="btn ghost"
          onClick={() => props.setTranscript(SAMPLE)}
          disabled={props.analyzing}
        >
          Load sample
        </button>

        {props.transcriptionAvailable && (
          <>
            <input
              ref={fileRef}
              type="file"
              accept="audio/*"
              hidden
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  setFileName(file.name);
                  props.onTranscribe(file);
                }
              }}
            />
            <button
              className="btn ghost"
              onClick={() => fileRef.current?.click()}
              disabled={props.transcribing}
            >
              {props.transcribing ? "Transcribing…" : "Upload audio"}
            </button>
            {fileName && <span className="file-name">{fileName}</span>}
          </>
        )}
      </div>
    </section>
  );
}
