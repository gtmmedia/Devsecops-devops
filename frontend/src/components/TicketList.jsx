import { PRIORITY_LABELS, STATUS_LABELS, ticketNumber, timeAgo } from "../format.js";

export default function TicketList({
  tickets,
  loading,
  selectedId,
  onSelect,
  query,
  onQuery,
  filtered,
  onNew,
}) {
  return (
    <div className="list-pane">
      <div className="search">
        <label htmlFor="search" className="sr-only">
          Search tickets
        </label>
        <input
          id="search"
          type="search"
          placeholder="Search by title or description"
          value={query}
          onChange={(e) => onQuery(e.target.value)}
        />
      </div>

      {!loading && tickets.length === 0 ? (
        <div className="empty">
          <p className="empty-title">{filtered ? "No tickets match" : "No tickets yet"}</p>
          <p>
            {filtered
              ? "Clear the search or pick another status."
              : "When a customer needs help, create a ticket and it shows up here."}
          </p>
          {!filtered && (
            <button type="button" className="btn btn-primary" onClick={onNew}>
              Create the first ticket
            </button>
          )}
        </div>
      ) : (
        <ul className="rows" aria-busy={loading}>
          {tickets.map((t) => (
            <li key={t.id}>
              <button
                type="button"
                className={`row prio-${t.priority}`}
                aria-current={t.id === selectedId ? "true" : undefined}
                onClick={() => onSelect(t.id)}
              >
                <span className="row-main">
                  <span className="row-title">{t.title}</span>
                  <span className="row-meta">
                    <span className="num">{ticketNumber(t.id)}</span>
                    <span>{t.requester_name}</span>
                    <span>{timeAgo(t.updated_at)}</span>
                  </span>
                </span>
                <span className="row-side">
                  <span className="status-text">
                    <span className={`dot dot-${t.status}`} aria-hidden="true" />
                    {STATUS_LABELS[t.status]}
                  </span>
                  <span className="row-flags">
                    <span className="sr-only">{PRIORITY_LABELS[t.priority]} priority. </span>
                    {t.comment_count > 0 && (
                      <span className="comments-n" title="Comments">
                        {t.comment_count} {t.comment_count === 1 ? "reply" : "replies"}
                      </span>
                    )}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
