"""Generate honest UI/evidence screenshots for the README.

Usage:
  python scripts/screenshots.py normal     # dashboard + ticket detail (stub AI)
  python scripts/screenshots.py failure    # AI failure banner (provider down -> 502)
  python scripts/screenshots.py qa         # build QA evidence HTML + screenshot it

Requires a running backend (:8000) and vite dev server (:5173). Playwright in
backend/.venv (pip install playwright); reuses the system Chrome via CHROME_HEADLESS.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROJ = "supportdesk_token"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = ROOT / "docs" / "screenshots"

CHROME_HEADLESS = {
    "executable_path": CHROME,
    "headless": True if os.environ.get("SHOW") != "1" else False,
    "args": ["--no-sandbox", "--disable-gpu"],
}


def login(page):
    page.goto("http://localhost:5173/login")
    page.fill('input[type="email"]', "agent@supportdesk.dev")
    page.fill('input[type="password"]', "agent1234")
    page.click('button:has-text("Log in")')
    page.wait_for_url("**/agent*")
    assert "/agent" in page.url, f"login failed: {page.url}"


def shot_normal(page):
    page.goto("http://localhost:5173/agent")
    page.wait_for_selector("table.ticket-table tbody tr", timeout=10000)
    page.set_viewport_size({"width": 1280, "height": 760})
    page.screenshot(path=str(OUT / "1-agent-dashboard.png"), full_page=False)

    # Ticket detail: AI analyze then suggest (stub provider, offline, safe draft).
    page.goto("http://localhost:5173/tickets/1")
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.wait_for_selector('button:has-text("AI analyze")', timeout=10000)
    page.click('button:has-text("AI analyze")')
    page.wait_for_selector("text=Confidence:", timeout=15000)
    page.wait_for_timeout(1500)
    try:
        page.click('button:has-text("Draft reply with AI")', timeout=8000)
        page.wait_for_selector("text=AI draft — unaudited", timeout=15000)
        page.wait_for_timeout(800)
    except Exception:
        pass
    page.set_viewport_size({"width": 1280, "height": 900})
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    Path("/tmp/sd_shot_debug.txt").write_text(
        "buttons=%r\nurl=%s\nerrors=%r\nbody=%r\nhtml_len=%d\n" % (
            page.locator("button").all_inner_texts(), page.url, errors,
            page.inner_text("body")[:400], len(page.content()),
        )
    )
    page.screenshot(path=str(OUT / "2-ticket-detail-ai.png"), full_page=True)
def shot_failure(page):
    # Frontend served on 5173; backend on 8000 = a failing AI provider (bad token).
    page.goto("http://localhost:5173/tickets/1")
    page.wait_for_selector('button:has-text("AI analyze")', timeout=10000)
    page.click('button:has-text("AI analyze")')
    page.wait_for_selector("text=AI support is unavailable", timeout=15000)
    page.wait_for_timeout(500)
    page.set_viewport_size({"width": 1280, "height": 820})
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "3-ai-failure-isolation.png"), full_page=True)


def qa_evidence() -> str:
    pytest = subprocess.run(
        [str(ROOT / "backend/.venv/bin/python"), "-m", "pytest"], cwd=ROOT / "backend",
        capture_output=True, text=True,
    ).stdout.strip().splitlines()[-1]
    eval_run = subprocess.run(
        [str(ROOT / "backend/.venv/bin/python"), "evaluation/evaluate.py"], cwd=ROOT,
        capture_output=True, text=True, env={**os.environ, "AI_PROVIDER": "stub"},
    ).stdout.strip()
    acc = next((l for l in eval_run.splitlines() if "Accuracy" in l), "Accuracy: n/a")
    m1 = next((l for l in eval_run.splitlines() if "Macro-F1" in l), "Macro-F1: n/a")
    return f"""{acc}
{m1}
---- pytest ----
{pytest}
---- evaluation (stub) ----
{eval_run}"""


def shot_qa():
    OUT.mkdir(parents=True, exist_ok=True)
    text = qa_evidence()
    html = OUT / "qa-evidence.html"
    html.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>body{font-family:monospace;background:#f7f8fa;padding:24px;}"
        "pre{background:#10141c;color:#d7e0f0;padding:16px;border-radius:6px;white-space:pre-wrap;}"
        "</style></head><body><h1>SupportDesk — QA evidence</h1>"
        "<p>Numbers below are captured from live tool runs (pytest / evaluation).</p>"
        f"<pre>{text}</pre></body></html>"
    )
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(**CHROME_HEADLESS)
        page = b.new_page(viewport={"width": 1280, "height": 1600})
        page.goto(html.as_uri())
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "4-qa-evidence.png"), full_page=True)
        b.close()
    print("wrote", html.name, "and 4-qa-evidence.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mode = "normal"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    if mode == "qa":
        shot_qa()
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(**CHROME_HEADLESS)
        ctx = b.new_context()
        page = ctx.new_page()
        login(page)
        if mode == "normal":
            shot_normal(page)
        elif mode == "failure":
            shot_failure(page)
        b.close()
    print("screenshots written to", OUT)


if __name__ == "__main__":
    main()