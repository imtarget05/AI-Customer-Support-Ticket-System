# Email Setup Guide

## Provider Configuration

The app uses a configurable `EMAIL_PROVIDER` environment variable with three modes:

| Mode | Behavior |
|------|----------|
| `stub` (default) | No email sent. Logs `"email stub to=<to> ticket=<id>"`. Used for CI/local development. |
| `log` | Same as `stub` but also logs to console. Useful for debugging without sending real email. |
| `smtp` | Sends via SMTP relay using `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`. |

## SMTP Configuration (smtp mode)

Set the following environment variables on Render/your host:

| Variable | Required | Description |
|----------|----------|-------------|
| `EMAIL_PROVIDER` | yes | Must be `"smtp"` |
| `SMTP_HOST` | yes | SMTP server hostname (e.g. `smtp.example.com`) |
| `SMTP_PORT` | no | Port, default `587` |
| `SMTP_USER` | yes | Username for SMTP auth |
| `SMTP_PASS` | yes | Password for SMTP auth |
| `SMTP_FROM` | yes | Sender email address (e.g. `noreply@example.com`) |
| `SMTP_TIMEOUT_S` | no | Connection timeout in seconds, default `5` |

## Important — Do NOT commit secrets

`SMTP_PASS` must **never** be stored in the repo. Add it via the Render dashboard or your host's env var system.

## How to test without sending real email

1. Set `EMAIL_PROVIDER=stub` (default) — no email sent, tests pass offline.
2. Set `EMAIL_PROVIDER=log` — email logged to console, no real email sent.
3. Set `EMAIL_PROVIDER=smtp` + fill in SMTP vars — send real email (test with a throwaway inbox first).

## SPF / DKIM / Deliverability

The app does **not** handle SPF/DKIM signing — that is the responsibility of your SMTP provider. To ensure deliverability:

- Configure SPF/DKIM in your DNS records for your domain
- Test by sending to a real inbox and checking the spam folder
- Some providers (SendGrid, Mailgun, Amazon SES) handle this for you; others (self-hosted Postfix) require manual configuration

## Rollback / Turn off email

To immediately stop sending email without a deploy:

```bash
# On Render: set EMAIL_PROVIDER=log or EMAIL_PROVIDER=stub
# Or via env var override on the host
EMAIL_PROVIDER=stub
```

Since `email_status` is an optional field on `MessageOut`, the frontend and API remain fully backward-compatible — existing tickets without `email_status` render normally.

## Backward Compatibility

- Existing tickets without `email_status` field render normally in the thread.
- The `email_status` field is optional in `MessageOut` — schema validation allows omitted field.
- Frontend badge only appears when `email_status` is `"sent"` or `"failed_logged"`.