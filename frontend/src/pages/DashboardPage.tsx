import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { DashboardStats, Ticket, TicketPage, TicketStatus } from "../types";
import { CATEGORY_LABELS, PRIORITY_LABELS, STATUS_LABELS } from "../types";

const STATUS_FILTERS: Array<TicketStatus | "all"> = [
  "all",
  "open",
  "in_progress",
  "waiting",
  "resolved",
  "closed",
];

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<TicketStatus | "all">("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<DashboardStats>("/api/dashboard/stats")
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load stats"));
  }, []);

  useEffect(() => {
    const qs = filter === "all" ? "" : `?status=${filter}`;
    api<TicketPage>(`/api/tickets${qs}`)
      .then((page) => {
        setTickets(page.items);
        setTotal(page.total);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load tickets"));
  }, [filter]);

  return (
    <div>
      <h1>Agent Dashboard</h1>
      {error && <p className="error">{error}</p>}
      {stats && (
        <div className="stat-grid">
          <div className="stat-card">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">Total</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.by_status["open"]}</span>
            <span className="stat-label">Open</span>
          </div>
          <div className="stat-card alert">
            <span className="stat-value">{stats.high_priority_open}</span>
            <span className="stat-label">High priority</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.by_status["waiting"]}</span>
            <span className="stat-label">Waiting</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.by_status["closed"]}</span>
            <span className="stat-label">Closed</span>
          </div>
        </div>
      )}

      <div className="toolbar">
        <label htmlFor="status-filter">Filter: </label>
        <select
          id="status-filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value as TicketStatus | "all")}
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s === "all" ? "All" : STATUS_LABELS[s]}
            </option>
          ))}
        </select>
        <span className="hint">{total} ticket(s)</span>
      </div>

      <table className="ticket-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Subject</th>
            <th>Customer</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>
                <Link to={`/tickets/${t.id}`}>{t.subject}</Link>
              </td>
              <td>{t.customer.name}</td>
              <td>{CATEGORY_LABELS[t.category]}</td>
              <td className={`priority-${t.priority}`}>{PRIORITY_LABELS[t.priority]}</td>
              <td>
                <span className={`badge badge-${t.status}`}>{STATUS_LABELS[t.status]}</span>
              </td>
            </tr>
          ))}
          {tickets.length === 0 && (
            <tr>
              <td colSpan={6}>No tickets match this filter.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
