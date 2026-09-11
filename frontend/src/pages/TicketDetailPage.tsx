import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type {
  Message,
  SimilarTicket,
  Suggestion,
  TicketDetail,
  TicketPriority,
  TicketStatus,
} from "../types";
import { CATEGORY_LABELS, PRIORITY_LABELS, STATUS_LABELS } from "../types";
import { statusAvailability, describeConfidence } from "../lib/ticketUi";
import { useAuth } from "../App";

const PRIORITIES: TicketPriority[] = ["low", "normal", "high", "urgent"];

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const isAgent = user?.role === "agent";

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [similar, setSimilar] = useState<SimilarTicket[]>([]);
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [reply, setReply] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [aiUnavailable, setAiUnavailable] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const confidence = ticket?.ai_confidence ? describeConfidence(ticket.ai_confidence) : { pct: 0, level: "low", text: "Chưa có đánh giá AI" };

  const load = useCallback(() => {
    api<TicketDetail>(`/api/tickets/${id}`)
      .then(setTicket)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load ticket"));
  }, [id]);

  useEffect(load, [load]);

  useEffect(() => {
    if (!isAgent || !ticket) return;
    api<{ items: SimilarTicket[] }>(`/api/tickets/${ticket.id}/similar`)
      .then((res) => setSimilar(res.items))
      .catch(() => setSimilar([]));
  }, [isAgent, ticket]);

  async function run<T>(fn: () => Promise<T>, okMessage?: string): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await fn();
      if (okMessage) setNotice(okMessage);
      return result;
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.message}` : String(err));
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function runAi<T>(fn: () => Promise<T>, okMessage?: string): Promise<T | undefined> {
    // AI is an enhancement, not the critical path: when it fails we isolate the
    // failure and keep the ticket fully usable for manual handling.
    setBusy(true);
    setError(null);
    setNotice(null);
    setAiUnavailable(null);
    try {
      const result = await fn();
      if (okMessage) setNotice(okMessage);
      return result;
    } catch (err) {
      setAiUnavailable(
        err instanceof ApiError && err.status === 502
          ? "AI support is unavailable right now. The ticket was not changed — review it and handle it manually below."
          : err instanceof ApiError ? `${err.status}: ${err.message}` : String(err)
      );
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function aiAnalyze() {
    await runAi(async () => {
      await api<TicketDetail>(`/api/tickets/${ticket!.id}/ai/analyze`, {
        method: "POST",
      });
      // Analyze returns the list shape (no messages) — refetch the detail view.
      load();
    }, "AI triage applied.");
  }

  async function aiSuggest() {
    await runAi(async () => {
      const res = await api<Suggestion>(`/api/tickets/${ticket!.id}/ai/suggest`, {
        method: "POST",
      });
      setSuggestion(res);
    });
  }

  async function transition(status: TicketStatus) {
    await run(async () => {
      await api<TicketDetail>(`/api/tickets/${ticket!.id}`, {
        method: "PATCH",
        body: { status },
      });
      // PATCH returns the list shape (no messages) — refetch the detail view.
      load();
    }, `Status changed to ${STATUS_LABELS[status]}.`);
  }

  async function changePriority(priority: TicketPriority) {
    await run(async () => {
      await api<TicketDetail>(`/api/tickets/${ticket!.id}`, {
        method: "PATCH",
        body: { priority },
      });
      load();
    }, `Priority set to ${PRIORITY_LABELS[priority]}.`);
  }

  async function sendReply(e: FormEvent) {
    e.preventDefault();
    const sent = await run<Message>(
      () =>
        api<Message>(`/api/tickets/${ticket!.id}/messages`, {
          method: "POST",
          body: { content: reply },
        }),
      "Reply sent."
    );
    if (sent) {
      setReply("");
      setSuggestion(null);
      load();
    }
  }

  if (!ticket) return <p>{error ?? "Loading…"}</p>;

  return (
    <div>
      <p className="hint">
        <Link to={isAgent ? "/agent" : "/"}>← Back</Link>
      </p>
      <h1>
        #{ticket.id} — {ticket.subject}
      </h1>
      {error && <p className="error">{error}</p>}
      {notice && <p className="notice">{notice}</p>}
      {aiUnavailable && <p data-testid="ai-unavailable" role="alert" className="ai-unavailable">{aiUnavailable}</p>}

      <div className="detail-grid">
        <div className="card">
          <h2>Ticket</h2>
          <p>
            <span className={`badge badge-${ticket.status}`}>{STATUS_LABELS[ticket.status]}</span>{" "}
            <span className={`priority-${ticket.priority}`}>
              {PRIORITY_LABELS[ticket.priority]}
            </span>{" "}
            · {CATEGORY_LABELS[ticket.category]}
          </p>
          <p>
            Customer: <strong>{ticket.customer.name}</strong> ({ticket.customer.email})
          </p>
          <p>{ticket.description}</p>

          {isAgent && (
            <>
              <h3>Agent controls</h3>
              <p className="btn-row" data-testid="status-flow">
                {statusAvailability(ticket.status).map(
                  ({ status: s, enabled, reason, current }) => (
                    <button
                      key={s}
                      disabled={busy || !enabled}
                      title={reason || undefined}
                      onClick={() => current ? null : transition(s)}
                    >
                      {current ? "●" : "→"} {STATUS_LABELS[s]}
                    </button>
                  )
                )}
              </p>
              <label className="inline">
                Priority:{" "}
                <select
                  value={ticket.priority}
                  disabled={busy}
                  onChange={(e) => changePriority(e.target.value as TicketPriority)}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {PRIORITY_LABELS[p]}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
        </div>

        <div className="card">
          <h2>🤖 AI Summary</h2>
          {ticket.ai_summary ? (
            <>
              <p>{ticket.ai_summary}</p>
              <p data-testid="ai-confidence" className={`hint confidence-${confidence.level}`}>{confidence.text}</p>
            </>
          ) : (
            <p className="hint">No AI analysis yet.</p>
          )}
          {isAgent && (
            <p className="hint">AI triage is unaudited — verify before acting on it.</p>
          )}
          {isAgent && (
            <button disabled={busy} onClick={aiAnalyze}>
              {ticket.ai_summary ? "Re-run AI analyze" : "Run AI analyze"}
            </button>
          )}
        </div>

        {isAgent && (
          <div className="card">
            <h2>🤖 Suggested Reply</h2>
            {suggestion ? (
              <>
                <textarea
                  value={suggestion.response}
                  rows={6}
                  onChange={(e) => setSuggestion({ ...suggestion, response: e.target.value })}
                />
                <p className="btn-row">
                  <button disabled={busy} onClick={() => setReply(suggestion.response)}>
                    Use in reply ↓
                  </button>
                  <button className="secondary" onClick={() => setSuggestion(null)}>
                    Dismiss
                  </button>
                </p>
                <p className="hint">
                  AI draft — unaudited. Verify policy, order numbers, and promises before sending. Nothing is sent until you send the reply.
                </p>
              </>
            ) : (
              <button disabled={busy} onClick={aiSuggest}>
                Draft reply with AI
              </button>
            )}
          </div>
        )}

        {isAgent && (
          <div className="card">
            <h2>🔗 Similar Resolved Tickets</h2>
            {similar.length === 0 ? (
              <p className="hint">No similar resolved tickets found.</p>
            ) : (
              <ul className="similar-list">
                {similar.map((s) => (
                  <li key={s.ticket_id}>
                    <Link to={`/tickets/${s.ticket_id}`}>
                      #{s.ticket_id} {s.subject}
                    </Link>{" "}
                    <span className="hint">({(100 * s.similarity).toFixed(0)}% match)</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Conversation</h2>
        {ticket.messages.length === 0 && <p className="hint">No replies yet.</p>}
        <div className="message-list" style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {ticket.messages.map((m) => (
            <div
              key={m.id}
              className={`message message-${m.sender.role}`}
              style={{ maxWidth: "75%" }}
            >
              <strong>{m.sender.name}</strong>{" "}
              <span className="hint">
                ({m.sender.role}) · {new Date(m.created_at).toLocaleString()}
              </span>
              <span className={`role-badge-${m.sender.role}`}>
                {m.sender.role === "agent" ? "Hỗ trợ" : "Khách hàng"}
              </span>
              <p>{m.content}</p>
            </div>
          ))}
        </div>

        {user ? (
          ticket.status !== "closed" ? (
            <form onSubmit={sendReply}>
              <label>
                {isAgent ? "Reply as agent" : "Reply"}
                <textarea
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  rows={4}
                  required
                />
              </label>
              <button type="submit" disabled={busy}>
                Send reply
              </button>
            </form>
          ) : (
            <p className="hint">This ticket is closed — replies are disabled.</p>
          )
        ) : (
          <p className="hint">
            <Link to="/login">Log in</Link> to reply.
          </p>
        )}
      </div>
    </div>
  );
}

