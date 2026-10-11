// Thin wrapper around fetch for the QuickDesk REST API.
// BASE is empty by default so calls go to the same origin (/api/...).
const BASE = import.meta.env.VITE_API_BASE ?? "";

function describeError(data, status) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => `${(e.loc || []).slice(1).join(".") || "input"}: ${e.msg}`)
      .join("; ");
  }
  return `The request failed (HTTP ${status}).`;
}

async function request(path, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Can't reach the QuickDesk API. Check that the backend is running.");
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(describeError(data, response.status));
  return data;
}

export const api = {
  listTickets({ status, q } = {}) {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (q) params.set("q", q);
    const qs = params.toString();
    return request(`/api/tickets${qs ? `?${qs}` : ""}`);
  },
  stats: () => request("/api/tickets/stats"),
  getTicket: (id) => request(`/api/tickets/${id}`),
  createTicket: (body) => request("/api/tickets", { method: "POST", body }),
  updateTicket: (id, body) => request(`/api/tickets/${id}`, { method: "PUT", body }),
  deleteTicket: (id) => request(`/api/tickets/${id}`, { method: "DELETE" }),
  addComment: (id, body) => request(`/api/tickets/${id}/comments`, { method: "POST", body }),
};
