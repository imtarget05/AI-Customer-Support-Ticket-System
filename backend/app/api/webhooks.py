"""Inbound provider webhooks (HMAC-signed).

Signature verification runs BEFORE any intake logic: requests with a
missing/invalid `X-Webhook-Signature` are rejected with 403. Only after
auth passes do well-formed-but-unroutable payloads return 200 `ignored`
(because webhook providers retry on 4xx — a 404/409 for `ignored` mail
would cause duplicate deliveries).
"""

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.config import _is_deployment, settings
from app.database import get_db
from app.services import inbound_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class InboundEmailPayload(BaseModel):
    model_config = {"populate_by_name": True}

    from_email: str | None = Field(default=None)
    from_: str | None = Field(default=None, alias="from")
    subject: str = ""
    body: str = Field(min_length=1)


def _webhook_secret() -> str:
    """Read at request time so env rotation/tests take effect without restart."""
    return os.getenv("INBOUND_WEBHOOK_SECRET", "") or settings.inbound_webhook_secret


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", "").strip().lower() == "production" or _is_deployment()


def _verify_signature(raw_body: bytes, signature: str | None) -> None:
    secret = _webhook_secret()
    if not secret:
        if _is_production():
            raise HTTPException(status_code=403, detail="webhook secret not configured")
        logger.warning("INBOUND_WEBHOOK_SECRET empty — skipping signature check (dev/test only)")
        return
    if not signature:
        raise HTTPException(status_code=403, detail="missing webhook signature")
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="invalid webhook signature")


@router.post("/inbound-email", status_code=200)
async def handle_inbound_email(request: Request, db: Session = Depends(get_db)) -> dict:
    """Accept SendGrid/SES-style inbound email and route it to ticket intake."""
    raw_body = await request.body()
    _verify_signature(raw_body, request.headers.get("X-Webhook-Signature"))
    try:
        payload = InboundEmailPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    from_email = payload.from_email or payload.from_
    if not from_email:
        return {"status": "ignored", "reason": "missing sender"}
    return inbound_email.process_inbound_email(db, from_email, payload.subject, payload.body)
