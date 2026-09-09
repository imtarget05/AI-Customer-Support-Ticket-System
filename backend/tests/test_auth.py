from tests.conftest import login, make_user


def test_login_success_returns_token_and_user(client, agent_user):
    res = client.post(
        "/api/auth/login", json={"email": "agent@test.dev", "password": "agentpw"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "agent@test.dev"
    assert body["user"]["role"] == "agent"


def test_login_wrong_password_401(client, agent_user):
    res = client.post("/api/auth/login", json={"email": "agent@test.dev", "password": "nope"})
    assert res.status_code == 401


def test_login_unknown_email_401(client):
    res = client.post("/api/auth/login", json={"email": "ghost@test.dev", "password": "x"})
    assert res.status_code == 401


def test_login_trims_email_case(client, agent_user):
    res = client.post(
        "/api/auth/login", json={"email": "  AGENT@test.dev ", "password": "agentpw"}
    )
    assert res.status_code == 200


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_current_user(client, customer_user):
    headers = login(client, "cust@test.dev", "custpw")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "cust@test.dev"


def test_me_rejects_garbage_token(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert res.status_code == 401


def test_password_hashing_roundtrip(db_session):
    user = make_user(db_session, email="hash@test.dev", name="H", role="customer", password="s3cret")
    assert user.password_hash != "s3cret"
    assert user.password_hash.startswith("pbkdf2_sha256$")
