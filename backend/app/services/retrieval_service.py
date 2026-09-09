"""Lightweight similar-ticket retrieval (embedding + cosine similarity).

Embeddings are stored in `ticket_embeddings` as JSON float lists; similarity
runs in Python, which is fine at MVP scale. The stub embedder is a hashed
bag-of-words vector — deterministic and dependency-free. Swap via
AI_EMBED_PROVIDER env later if a real embedding model is wired in.
"""

import hashlib
import json
import math
import re

from sqlalchemy.orm import Session

from app.models import Ticket, TicketEmbedding

EMBED_DIM = 128
SIMILAR_STATUSES = ("resolved", "closed")
TOKEN_RE = re.compile(r"[a-z0-9]+")


def embed(text: str) -> list[float]:
    """Hashed bag-of-words, L2-normalized. Deterministic."""
    vector = [0.0] * EMBED_DIM
    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBED_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [round(v / norm, 6) for v in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 0.0 if norm == 0 else round(dot / norm, 4)


def _encode(vector: list[float]) -> str:
    return json.dumps(vector)


def _decode(raw: str) -> list[float]:
    return json.loads(raw)


def ensure_embedding(db: Session, ticket: Ticket) -> list[float]:
    """Compute and persist the ticket embedding if absent; return the vector."""
    row = db.get(TicketEmbedding, ticket.id)
    if row is not None:
        return _decode(row.embedding)
    vector = embed(f"{ticket.subject} {ticket.description}")
    db.add(TicketEmbedding(ticket_id=ticket.id, embedding=_encode(vector)))
    db.commit()
    return vector


def find_similar_tickets(
    db: Session, ticket: Ticket, limit: int = 3, min_similarity: float = 0.05
) -> list[dict]:
    """Most similar resolved/closed tickets (never the ticket itself)."""
    target = ensure_embedding(db, ticket)
    candidates = (
        db.query(Ticket)
        .filter(Ticket.id != ticket.id)
        .filter(Ticket.status.in_(SIMILAR_STATUSES))
        .all()
    )
    scored = [
        {
            "ticket_id": candidate.id,
            "subject": candidate.subject,
            "status": candidate.status,
            "similarity": cosine_similarity(target, ensure_embedding(db, candidate)),
        }
        for candidate in candidates
    ]
    scored = [s for s in scored if s["similarity"] >= min_similarity]
    scored.sort(key=lambda s: s["similarity"], reverse=True)
    return scored[:limit]
