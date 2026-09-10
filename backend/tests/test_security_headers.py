"""Security headers test for nginx configuration."""

from pathlib import Path


def test_security_headers_present():
    """Verify nginx.conf contains required security headers (SonarQube fix)."""
    # Test file: backend/tests/test_security_headers.py
    # Repo root: 2 levels up from test file
    test_dir = Path(__file__).parent.parent  # → backend/
    repo_root = test_dir.parent  # → repo root
    nginx_conf = (repo_root / "frontend" / "nginx.conf").read_text()

    required_headers = [
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Content-Security-Policy",
    ]
    for header in required_headers:
        assert header in nginx_conf, f"Missing {header} in frontend/nginx.conf"