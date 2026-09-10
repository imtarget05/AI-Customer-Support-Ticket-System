FROM python:3.12-slim AS builder

WORKDIR /srv
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /srv
COPY --from=builder /root/.local /root/.local
COPY backend/ ./backend/
COPY evaluation/ ./evaluation/

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /srv
ENV PATH=/root/.local/bin:$PATH

USER appuser

ENV AI_PROVIDER=stub \
    AI_EMBED_PROVIDER=bow \
    DATABASE_URL=sqlite:///./supportdesk.db \
    JWT_SECRET=dev-secret-change-me \
    ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
