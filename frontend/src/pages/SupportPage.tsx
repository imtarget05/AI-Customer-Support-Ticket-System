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

  if (created) {
    return (
      <div className="card narrow">
        <h1>Ticket #{created.id} created ✅</h1>
        <p>
          We received your request: <strong>{created.subject}</strong>. Our team will get back to
          you soon.
        </p>
        <p>
          <Link to={`/tickets/${created.id}`}>View ticket status →</Link>
        </p>
        <button onClick={() => setCreated(null)}>Submit another ticket</button>
      </div>
    );
  }

  return (
    <div className="card narrow">
      <h1>Submit a Ticket</h1>
      {!user && (
        <p className="hint">
          Have an account? <Link to="/login">Log in</Link> — or just leave your email below.
        </p>
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
    </div>
  );
}
