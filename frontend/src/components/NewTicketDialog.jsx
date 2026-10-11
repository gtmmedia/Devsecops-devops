import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { PRIORITY_LABELS } from "../format.js";

const EMPTY = {
  title: "",
  description: "",
  priority: "medium",
  requester_name: "",
  requester_email: "",
};

export default function NewTicketDialog({ open, onClose, onCreated }) {
  const ref = useRef(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setForm(EMPTY);
      setError("");
      dialog.showModal();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const ticket = await api.createTicket(form);
      onCreated(ticket);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <dialog ref={ref} className="dialog" onClose={onClose} aria-labelledby="new-title">
      <form onSubmit={submit} className="form">
        <h2 id="new-title">New ticket</h2>

        <label>
          What's the problem?
          <input
            required
            minLength={3}
            maxLength={200}
            value={form.title}
            onChange={set("title")}
            placeholder="e.g. Invoice shows the wrong amount"
          />
        </label>

        <label>
          Details
          <textarea
            required
            rows={4}
            maxLength={5000}
            value={form.description}
            onChange={set("description")}
            placeholder="What happened, and what did you expect?"
          />
        </label>

        <fieldset className="segmented">
          <legend>Priority</legend>
          {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
            <label key={value} className={`seg-opt prio-opt-${value}`}>
              <input
                type="radio"
                name="priority"
                value={value}
                checked={form.priority === value}
                onChange={set("priority")}
              />
              <span>{label}</span>
            </label>
          ))}
        </fieldset>

        <div className="two">
          <label>
            Requester name
            <input required maxLength={100} value={form.requester_name} onChange={set("requester_name")} />
          </label>
          <label>
            Requester email
            <input
              required
              type="email"
              value={form.requester_email}
              onChange={set("requester_email")}
            />
          </label>
        </div>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Creating" : "Create ticket"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
