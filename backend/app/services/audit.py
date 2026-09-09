"""Audit trail for AI-assisted support operations.

This module provides audit logging for all AI operations, ensuring
traceability and compliance. The audit trail captures:
    - AI classification and drafting decisions
    - Confidence levels and routing decisions
    - Human review actions
    - Knowledge base evidence used
    - Workflow state transitions
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: float
    action: str
    ticket_id: int
    workflow_id: str
    stage: str
    details: dict[str, Any] = field(default_factory=dict)
    actor: str = "system"


class AuditTrail:
    """Audit trail for AI operations.

    Provides structured logging of all AI operations for compliance,
    debugging, and quality improvement.
    """

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def log(
        self,
        action: str,
        ticket_id: int,
        workflow_id: str,
        stage: str,
        details: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> AuditEntry:
        """Log an audit entry.

        Args:
            action: The action performed.
            ticket_id: The ticket ID.
            workflow_id: The workflow ID.
            stage: The workflow stage.
            details: Additional details.
            actor: The actor (system, agent name, etc.).

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action=action,
            ticket_id=ticket_id,
            workflow_id=workflow_id,
            stage=stage,
            details=details or {},
            actor=actor,
        )
        self._entries.append(entry)

        # Also log to the application logger
        logger.info(
            "AUDIT: ticket=%d workflow=%s stage=%s action=%s actor=%s",
            ticket_id, workflow_id, stage, action, actor,
        )

        return entry

    def get_entries(
        self,
        ticket_id: int | None = None,
        workflow_id: str | None = None,
        limit: int | None = None,
    ) -> list[AuditEntry]:
        """Get audit entries, optionally filtered.

        Args:
            ticket_id: Filter by ticket ID.
            workflow_id: Filter by workflow ID.
            limit: Maximum number of entries to return.

        Returns:
            List of matching AuditEntry objects.
        """
        entries = self._entries

        if ticket_id is not None:
            entries = [e for e in entries if e.ticket_id == ticket_id]

        if workflow_id is not None:
            entries = [e for e in entries if e.workflow_id == workflow_id]

        # Sort by timestamp (most recent first)
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)

        if limit is not None:
            entries = entries[:limit]

        return entries

    def get_stats(self) -> dict[str, Any]:
        """Return statistics about the audit trail."""
        if not self._entries:
            return {"total_entries": 0}

        actions: dict[str, int] = {}
        stages: dict[str, int] = {}
        for entry in self._entries:
            actions[entry.action] = actions.get(entry.action, 0) + 1
            stages[entry.stage] = stages.get(entry.stage, 0) + 1

        return {
            "total_entries": len(self._entries),
            "actions": actions,
            "stages": stages,
            "oldest_entry": min(e.timestamp for e in self._entries),
            "newest_entry": max(e.timestamp for e in self._entries),
        }

    def clear(self) -> None:
        """Clear all audit entries (for testing)."""
        self._entries = []


# Singleton instance
_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    """Get or create the singleton AuditTrail instance."""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail


def reset_audit_trail() -> None:
    """Reset the singleton (for testing)."""
    global _audit_trail
    _audit_trail = AuditTrail()