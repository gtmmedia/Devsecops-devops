import { STATUS_LABELS } from "../format.js";

const ORDER = ["open", "in_progress", "resolved", "closed"];

// The queue at a glance: one bar showing how tickets split across statuses.
// The legend under it doubles as the status filter.
export default function QueueBar({ stats, active, onSelect }) {
  const total = stats?.total ?? 0;
  return (
    <section className="queue" aria-label="Ticket queue overview">
      <div className="queue-head">
        <h1 className="queue-title">
          {stats ? (
            <>
              <span className="queue-count">{total}</span> {total === 1 ? "ticket" : "tickets"}
            </>
          ) : (
            "Loading queue"
          )}
        </h1>
        {stats && stats.high_priority_open > 0 && (
          <p className="queue-alert">
            {stats.high_priority_open} high priority still need an answer
          </p>
        )}
      </div>

      <div className="queue-bar" role="img" aria-label="Tickets by status">
        {ORDER.map((s) => {
          const n = stats?.[s] ?? 0;
          return n > 0 ? (
            <span key={s} className={`seg seg-${s}`} style={{ flexGrow: n }} />
          ) : null;
        })}
        {total === 0 && <span className="seg seg-empty" style={{ flexGrow: 1 }} />}
      </div>

      <div className="queue-legend" role="group" aria-label="Filter by status">
        <button
          type="button"
          className="chip"
          aria-pressed={active === "all"}
          onClick={() => onSelect("all")}
        >
          All <b>{total}</b>
        </button>
        {ORDER.map((s) => (
          <button
            key={s}
            type="button"
            className="chip"
            aria-pressed={active === s}
            onClick={() => onSelect(s)}
          >
            <span className={`dot dot-${s}`} aria-hidden="true" />
            {STATUS_LABELS[s]} <b>{stats?.[s] ?? 0}</b>
          </button>
        ))}
      </div>
    </section>
  );
}
