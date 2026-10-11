import { useEffect, useState } from "react";
import { api } from "../api.js";
import { PRIORITY_LABELS, STATUS_LABELS, ticketNumber, timeAgo } from "../format.js";

const AUTHOR_KEY = "quickdesk.author";

function readAuthor() {
  try {
    return localStorage.getItem(AUTHOR_KEY) || "";
  } catch {
    return "";
  }
}

export default function TicketDetail({ id, onBack, onChanged, onDeleted, notify }) {
  const [ticket, setTicket] = useState(null);
  const [form, setForm] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [author, setAuthor] = useState(readAuthor);
  const [body, setBody] = useState("");
  const [posting, setPosting] = useState(false);

  async function load() {
    try {
      const t = await api.getTicket(id);
      setTicket(t);
      setForm({
        title: t.title,
        description: t.description,
        status: t.status,
        priority: t.priority,
        assignee: t.assignee ?? "",
      });
      setLoadError("");
    } catch (err) {
      setLoadError(err.message);
    }
  }

  useEffect(() => {
    setTicket(null);
    setForm(null);
    setError("");
    setBody("");
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loadError) {
    return (
      <div className="detail-pane">
        <button type="button" className="back" onClick={onBack}>
          Back to tickets
        </button>
        <p className="error" role="alert">
          {loadError}
        </p>
      </div>
    );
  }
  if (!ticket || !form) {
    return (
      <div className="detail-pane">
        <p className="muted">Loading ticket</p>
      </div>
    );
  }

  const frozen = ticket.status === "closed";
  const dirty = ["title", "description", "status", "priority"].some((k) => form[k] !== ticket[k]) ||
    form.assignee !== (ticket.assignee ?? "");
  // Mirrors the API rule: a closed ticket can only be reopened, not edited.
  const canSave = dirty && !(frozen && form.status === "closed");
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.updateTicket(id, {
        ...form,
        assignee: form.assignee.trim() || null,
      });
      await load();
      onChanged();
      notify(`Saved ${ticketNumber(id)}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Delete ${ticketNumber(id)} and its comments? This can't be undone.`)) return;
    try {
      await api.deleteTicket(id);
      onDeleted(id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function postComment(e) {
    e.preventDefault();
    setPosting(true);
    setError("");
    try {
      await api.addComment(id, { author, body });
      try {
        localStorage.setItem(AUTHOR_KEY, author);
      } catch {
        /* storage unavailable: not a problem */
      }
      setBody("");
      await load();
      onChanged();
      notify("Comment added");
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="detail-pane">
      <button type="button" className="back" onClick={onBack}>
        Back to tickets
      </button>

      <header className={`detail-head prio-${ticket.priority}`}>
        <p className="detail-sub">
          <span className="num">{ticketNumber(ticket.id)}</span>
          <span>
            from {ticket.requester_name} ({ticket.requester_email})
          </span>
          <span>opened {timeAgo(ticket.created_at)}</span>
        </p>
        <h2>{ticket.title}</h2>
      </header>

      <form className="form" onSubmit={save}>
        {frozen && (
          <p className="note">
            This ticket is closed. Change the status to reopen it, then edit.
          </p>
        )}

        <label>
          Title
          <input
            value={form.title}
            onChange={set("title")}
            minLength={3}
            maxLength={200}
            required
            disabled={frozen}
          />
        </label>
        <label>
          Description
          <textarea
            rows={4}
            value={form.description}
            onChange={set("description")}
            maxLength={5000}
            required
            disabled={frozen}
          />
        </label>
        <div className="three">
          <label>
            Status
            <select value={form.status} onChange={set("status")}>
              {Object.entries(STATUS_LABELS).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <label>
            Priority
            <select value={form.priority} onChange={set("priority")} disabled={frozen}>
              {Object.entries(PRIORITY_LABELS).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <label>
            Assigned to
            <input
              value={form.assignee}
              onChange={set("assignee")}
              maxLength={100}
              placeholder="Unassigned"
              disabled={frozen}
            />
          </label>
        </div>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <div className="actions spread">
          <button type="button" className="btn btn-danger" onClick={remove}>
            Delete ticket
          </button>
          <button type="submit" className="btn btn-primary" disabled={!canSave || saving}>
            {saving ? "Saving" : "Save changes"}
          </button>
        </div>
      </form>

      <section className="thread" aria-label="Comments">
        <h3>
          Conversation <span className="muted">({ticket.comments.length})</span>
        </h3>
        {ticket.comments.length === 0 ? (
          <p className="muted">No replies yet. Add the first one below.</p>
        ) : (
          <ol className="comments">
            {ticket.comments.map((c) => (
              <li key={c.id}>
                <p className="comment-head">
                  <b>{c.author}</b> <span className="muted">{timeAgo(c.created_at)}</span>
                </p>
                <p className="comment-body">{c.body}</p>
              </li>
            ))}
          </ol>
        )}

        <form className="form comment-form" onSubmit={postComment}>
          <label>
            Your name
            <input required maxLength={100} value={author} onChange={(e) => setAuthor(e.target.value)} />
          </label>
          <label>
            Reply
            <textarea
              required
              rows={3}
              maxLength={5000}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write a reply for this ticket"
            />
          </label>
          <div className="actions">
            <button type="submit" className="btn btn-primary" disabled={posting}>
              {posting ? "Posting" : "Add comment"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
