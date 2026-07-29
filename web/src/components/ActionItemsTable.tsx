import type { ActionItem, ActionStatus, Priority } from "../types";

interface Props {
  items: ActionItem[];
  onChange: (items: ActionItem[]) => void;
}

const PRIORITIES: Priority[] = ["low", "medium", "high"];
const STATUSES: ActionStatus[] = ["open", "in_progress", "done"];

export function ActionItemsTable({ items, onChange }: Props) {
  if (items.length === 0) {
    return <p className="empty">No action items were identified.</p>;
  }

  function update(id: string, patch: Partial<ActionItem>) {
    onChange(items.map((it) => (it.id === id ? { ...it, ...patch } : it)));
  }

  return (
    <div className="table-wrap">
      <table className="action-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Owner</th>
            <th>Due</th>
            <th>Priority</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className={item.status === "done" ? "done-row" : ""}>
              <td className="task-cell">{item.task}</td>
              <td>{item.owner ?? <span className="muted">—</span>}</td>
              <td>{item.due_date ?? <span className="muted">—</span>}</td>
              <td>
                <select
                  className={`pill priority-${item.priority}`}
                  value={item.priority}
                  onChange={(e) =>
                    update(item.id, { priority: e.target.value as Priority })
                  }
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <select
                  className={`pill status-${item.status}`}
                  value={item.status}
                  onChange={(e) =>
                    update(item.id, { status: e.target.value as ActionStatus })
                  }
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replace("_", " ")}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
