import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import NewTicketDialog from "./components/NewTicketDialog.jsx";
import QueueBar from "./components/QueueBar.jsx";
import TicketDetail from "./components/TicketDetail.jsx";
import TicketList from "./components/TicketList.jsx";
import { ticketNumber } from "./format.js";

function useDebounced(value, ms = 250) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

export default function App() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounced(query.trim());
  const [selectedId, setSelectedId] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const toastTimer = useRef(null);

  const notify = useCallback((message) => {
    setToast(message);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 3500);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [list, s] = await Promise.all([
        api.listTickets({
          status: filter === "all" ? undefined : filter,
          q: debouncedQuery || undefined,
        }),
        api.stats(),
      ]);
      setTickets(list);
      setStats(s);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filter, debouncedQuery]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const filtered = filter !== "all" || debouncedQuery !== "";

  return (
    <div className={`app ${selectedId ? "has-selection" : ""}`}>
      <header className="topbar">
        <a className="brand" href="/" aria-label="QuickDesk home">
          <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="currentColor" />
            <path
              d="M8 11.5h16v3.2a2.3 2.3 0 0 0 0 4.6v3.2H8v-3.2a2.3 2.3 0 0 0 0-4.6z"
              fill="#fff"
            />
          </svg>
          QuickDesk
        </a>
        <button type="button" className="btn btn-primary" onClick={() => setShowNew(true)}>
          New ticket
        </button>
      </header>

      <main className="shell">
        <QueueBar stats={stats} active={filter} onSelect={setFilter} />

        {error && (
          <p className="banner" role="alert">
            {error}{" "}
            <button type="button" className="link" onClick={refresh}>
              Try again
            </button>
          </p>
        )}

        <div className="workspace">
          <TicketList
            tickets={tickets}
            loading={loading}
            selectedId={selectedId}
            onSelect={setSelectedId}
            query={query}
            onQuery={setQuery}
            filtered={filtered}
            onNew={() => setShowNew(true)}
          />

          <section className="detail-wrap" aria-live="polite">
            {selectedId ? (
              <TicketDetail
                id={selectedId}
                onBack={() => setSelectedId(null)}
                onChanged={refresh}
                onDeleted={(id) => {
                  setSelectedId(null);
                  refresh();
                  notify(`Deleted ${ticketNumber(id)}`);
                }}
                notify={notify}
              />
            ) : (
              <div className="detail-empty">
                <p className="empty-title">Pick a ticket to read it</p>
                <p>Its conversation, status and owner appear here.</p>
              </div>
            )}
          </section>
        </div>
      </main>

      <NewTicketDialog
        open={showNew}
        onClose={() => setShowNew(false)}
        onCreated={(ticket) => {
          setShowNew(false);
          setFilter("all");
          setQuery("");
          setSelectedId(ticket.id);
          refresh();
          notify(`Created ${ticketNumber(ticket.id)}`);
        }}
      />

      <div className="toast" role="status">
        {toast}
      </div>
    </div>
  );
}
