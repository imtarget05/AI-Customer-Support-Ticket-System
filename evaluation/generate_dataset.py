"""One-off generator for evaluation/tickets.json (not part of the runtime app).

Produces ~100 realistic labeled tickets across 5 categories by combining
hand-written scenario templates with concrete variations (ids, devices, apps).
"""
import json
import random
from pathlib import Path

random.seed(42)

ORDERS = [f"#{n}" for n in range(8100, 8180)]
APPS = ["iOS app", "Android app", "web dashboard", "desktop client"]
DEVICES = ["iPhone 14", "Pixel 7", "MacBook Air", "Windows laptop", "iPad"]
DAYS = ["3 days", "a week", "two weeks", "a month"]

T = []  # (subject, description, category)

# ---------------- authentication (20) ----------------
for dev, app in zip(DEVICES, APPS):
    T.append((
        "Cannot reset my password",
        f"I clicked 'Forgot password' four times on the {app} and no reset email ever arrives. "
        "I already checked spam and junk folders. Nothing works.",
        "authentication"))
    T.append((
        "Account locked after too many login attempts",
        f"My account got locked on my {dev} after I typed the password wrong a few times. "
        "I know the password now but it still says account locked. Please unlock it.",
        "authentication"))
    T.append((
        "Two-factor codes not accepted",
        f"The 2FA codes from my authenticator app are rejected every time I try to sign in on the {app}. "
        f"This started {random.choice(DAYS).capitalize()} ago. I am locked out completely.",
        "authentication"))
    T.append((
        "Logged out of every device and cannot log back in",
        f"I was suddenly signed out everywhere. Logging in again just bounces me back to the login "
        f"screen on {dev}. My password is definitely correct.",
        "authentication"))

# ---------------- payment (20) ----------------
for i, order in enumerate(ORDERS[:10]):
    T.append((
        f"Payment charged twice for order {order}",
        f"Order {order} shows two identical charges of $59.00 on my card but I only received one "
        "confirmation email. Please refund the duplicate charge.",
        "payment"))
for i, order in enumerate(ORDERS[10:15]):
    T.append((
        f"Card declined at checkout for order {order}",
        f"My card keeps getting declined at checkout for order {order} even though the card works "
        "everywhere else. I tried two different cards and got the same error.",
        "payment"))
for i, order in enumerate(ORDERS[15:20]):
    T.append((
        f"Invoice amount is wrong for order {order}",
        f"The invoice for order {order} lists a higher total than the price shown at checkout. "
        "I was billed the wrong amount and need this corrected.",
        "payment"))

# ---------------- refund (20) ----------------
for i in range(8):
    T.append((
        f"Refund status still processing for return {random.choice(ORDERS)}",
        f"I shipped the returned item {random.choice(DAYS)} ago and the refund status still says "
        "processing. When will the money reach my account?",
        "refund"))
for i in range(6):
    T.append((
        "Refund not received after cancelled subscription",
        f"I cancelled my subscription {random.choice(DAYS)} ago but was still charged for the next "
        "cycle. I want a refund of that charge since I cancelled in time.",
        "refund"))
for i in range(6):
    T.append((
        "Wrong item delivered — need refund",
        f"The package arrived today but contains the wrong item entirely. I want to return it and "
        f"get a refund for the order {random.choice(ORDERS)}.",
        "refund"))

# ---------------- technical (20) ----------------
for dev, app in zip(DEVICES, APPS):
    T.append((
        f"{app.capitalize()} crashes on startup",
        f"Since the latest update the {app} crashes immediately on my {dev} every time I open it. "
        "Reinstalling did not help.",
        "technical"))
    T.append((
        f"Dashboard shows stale data on {dev}",
        f"The dashboard on my {dev} has not updated in days while the mobile view shows new data. "
        "Seems like a sync issue after the recent release.",
        "technical"))
    T.append((
        f"Export button throws an error on {dev}",
        f"Clicking 'Export' in the {app} gives a red error toast and nothing downloads. "
        "Happens with every report I try.",
        "technical"))
    T.append((
        f"Notifications never arrive on {dev}",
        f"Push notifications stopped working on the {app} for my {dev} about {random.choice(DAYS)} ago. "
        "Notification permissions are enabled in settings.",
        "technical"))

# ---------------- other (20) ----------------
for i in range(8):
    T.append((
        "Feature idea: dark mode",
        "It would be great if the dashboard had a dark mode option for evening shifts. "
        "Not urgent, just a suggestion from a daily user.",
        "other"))
for i in range(6):
    T.append((
        "Question about team plans",
        "Do you offer discounts for a team of around 15 people? I could not find pricing details "
        "for team accounts on the website.",
        "other"))
for i in range(6):
    T.append((
        "How do I change my account email?",
        "I want to move my account to a new email address because I am leaving my current company. "
        "Where can I do that?",
        "other"))

random.shuffle(T)
data = [
    {"id": i + 1, "subject": s, "description": d, "expected_category": c}
    for i, (s, d, c) in enumerate(T)
]
out = Path(__file__).resolve().parents[1] / "evaluation" / "tickets.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(data, indent=2) + "\n")

from collections import Counter
print(f"wrote {len(data)} tickets to {out}")
print(Counter(t["expected_category"] for t in data))
