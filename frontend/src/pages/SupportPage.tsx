import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Ticket } from "../types";
import { useAuth } from "../App";

export default function SupportPage() {
  const { user } = useAuth();
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [created, setCreated] = useState<Ticket | null>(null);
  const [history, setHistory] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body: Record<string, string> = { subject, description };
      if (!user) {
        body.customer_email = email;
        body.customer_name = name;
      }
      const ticket = await api<Ticket>("/api/tickets", { method: "POST", body });
      setHistory((h) => [ticket, ...h]);
      setCreated(ticket);
      setSubject("");
      setDescription("");
      setEmail("");
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit ticket");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card narrow">
      <h1>Submit a Ticket</h1>
      {user && (
        <p className="hint">Bạn đang gửi với tài khoản <strong>{user.email}</strong> — không cần nhập email.</p>
      )}
      {!user && (
        <>
          <p className="hint">Gửi ẩn danh — nhập email để nhận phản hồi</p>
          <label>
            Your email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Your name (optional)
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
        </>
      )}
      <form onSubmit={onSubmit}>
        <label>
          Subject
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            minLength={3}
            maxLength={200}
            required
          />
        </label>
        <label>
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={6}
            minLength={10}
            maxLength={5000}
            required
          />
        </label>
        {!user && (
          <>
            <label>
              Your email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              Your name (optional)
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
          </>
        )}
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Submitting…" : "Submit ticket"}
        </button>
      </form>
      {created && (
        <div data-testid="success-card" className="card narrow">
          <h1>Ticket #{created.id} created ✅</h1>
          <p>
            We received your request: <strong>{created.subject}</strong>. Our team will get back to
            you soon.
          </p>
          <p>
            <Link to={`/tickets/${created.id}`}>Xem trạng thái →</Link>
          </p>
        </div>
      )}
      {history.length > 0 && (
        <div data-testid="history-panel" className="card narrow">
          <h3>Lịch sử gửi ticket</h3>
          <ul>
            {history.map((t) => (
              <li key={t.id}>#{t.id} - {t.subject}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}