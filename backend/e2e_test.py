import os
import secrets

os.environ['DATABASE_URL'] = 'sqlite:///./e2e_full_test.db'
os.environ['JWT_SECRET'] = secrets.token_urlsafe(32)
os.environ['AI_PROVIDER'] = 'cloudflare'
from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    db.add(User(name='Customer', email='cust@test.dev', password_hash=hash_password('pw'), role='customer'))
    db.add(User(name='Agent', email='agent@test.dev', password_hash=hash_password('pw'), role='agent'))
    db.commit()
finally:
    db.close()

client = TestClient(app)

# Test 1: Login
print("=== TEST 1: Login ===")
r = client.post('/api/auth/login', json={'email':'cust@test.dev','password':'pw'})
print(f"Customer login: {r.status_code} {r.text[:200]}")
token = r.json().get('access_token','') if r.status_code == 200 else ''
headers = {'Authorization': f'Bearer {token}'}

# Test 2: Create ticket
print("\n=== TEST 2: Create ticket ===")
r2 = client.post('/api/tickets', json={'subject':'Login issue','description':'Cannot sign in','customer_email':'cust@test.dev','customer_name':'Customer'}, headers=headers)
print(f"Create ticket: {r2.status_code} {r2.text[:300]}")
tid = r2.json().get('id') if r2.status_code == 201 else None

# Test 3: Get tickets list
print("\n=== TEST 3: Get tickets ===")
r3 = client.get('/api/tickets', headers=headers)
print(f"List tickets: {r3.status_code} {r3.text[:200]}")

# Test 4: Get ticket detail
if tid:
    print("\n=== TEST 4: Get ticket detail ===")
    r4 = client.get(f'/api/tickets/{tid}', headers=headers)
    print(f"Ticket detail: {r4.status_code} {r4.text[:300]}")

# Test 5: Agent login
print("\n=== TEST 5: Agent login ===")
r_agent = client.post('/api/auth/login', json={'email':'agent@test.dev','password':'pw'})
print(f"Agent login: {r_agent.status_code}")
agent_token = r_agent.json().get('access_token','') if r_agent.status_code == 200 else ''
agent_headers = {'Authorization': f'Bearer {agent_token}'}

# Test 6: AI analyze
if tid:
    print("\n=== TEST 6: AI analyze ===")
    r6 = client.post(f'/api/tickets/{tid}/ai/analyze', headers=agent_headers)
    print(f"AI analyze: {r6.status_code} {r6.text[:200]}")

# Test 7: AI suggest
if tid:
    print("\n=== TEST 7: AI suggest ===")
    r7 = client.post(f'/api/tickets/{tid}/ai/suggest', headers=agent_headers)
    print(f"AI suggest: {r7.status_code} {r7.json().get('response','')[:100]}")

# Test 8: Similar tickets
if tid:
    print("\n=== TEST 8: Similar tickets ===")
    r8 = client.get(f'/api/tickets/{tid}/similar', headers=agent_headers)
    print(f"Similar: {r8.status_code} {r8.text[:200]}")

# Test 9: Workflow
if tid:
    print("\n=== TEST 9: Workflow ===")
    r9 = client.post(f'/api/tickets/{tid}/ai/workflow', headers=agent_headers)
    print(f"Workflow: {r9.status_code} {r9.text[:300]}")

# Test 10: Metrics
print("\n=== TEST 10: Metrics ===")
r10 = client.get('/api/metrics', headers=agent_headers)
print(f"Metrics: {r10.status_code} {r10.text[:200]}")

# Test 11: Send reply
if tid:
    print("\n=== TEST 11: Send reply ===")
    r11 = client.post(f'/api/tickets/{tid}/messages', json={'content':'We are looking into this.'}, headers=agent_headers)
    print(f"Reply: {r11.status_code} {r11.text[:200]}")

# Test 12: Transition status
if tid:
    print("\n=== TEST 12: Transition status ===")
    r12 = client.patch(f'/api/tickets/{tid}', json={'status':'in_progress'}, headers=agent_headers)
    print(f"Transition: {r12.status_code} {r12.text[:200]}")

# Test 13: Illegal transition
if tid:
    print("\n=== TEST 13: Illegal transition (open -> closed) ===")
    r13 = client.patch(f'/api/tickets/{tid}', json={'status':'closed'}, headers=agent_headers)
    print(f"Illegal transition: {r13.status_code} {r13.text[:200]}")

# Test 14: Dashboard stats
print("\n=== TEST 14: Dashboard stats ===")
r14 = client.get('/api/dashboard/stats', headers=agent_headers)
print(f"Dashboard: {r14.status_code} {r14.text[:200]}")

# Test 15: Invalid login
print("\n=== TEST 15: Invalid login ===")
r15 = client.post('/api/auth/login', json={'email':'cust@test.dev','password':'wrong'})
print(f"Invalid login: {r15.status_code} {r15.text[:200]}")

# Test 16: Access without token
print("\n=== TEST 16: Access without token ===")
r16 = client.get('/api/tickets')
print(f"No token: {r16.status_code} {r16.text[:200]}")

# Test 17: Customer trying agent endpoint
print("\n=== TEST 17: Customer access agent endpoint ===")
r17 = client.get('/api/dashboard/stats', headers=headers)
print(f"Customer access stats: {r17.status_code} {r17.text[:200]}")

# Test 18: AI suggest with closed ticket
if tid:
    # First close the ticket
    client.patch(f'/api/tickets/{tid}', json={'status':'in_progress'}, headers=agent_headers)
    client.patch(f'/api/tickets/{tid}', json={'status':'resolved'}, headers=agent_headers)
    client.patch(f'/api/tickets/{tid}', json={'status':'closed'}, headers=agent_headers)
    print("\n=== TEST 18: AI suggest on closed ticket ===")
    r18 = client.post(f'/api/tickets/{tid}/ai/suggest', headers=agent_headers)
    print(f"AI suggest closed: {r18.status_code} {r18.text[:200]}")

# Test 19: AI analyze on closed ticket
if tid:
    print("\n=== TEST 19: AI analyze on closed ticket ===")
    r19 = client.post(f'/api/tickets/{tid}/ai/analyze', headers=agent_headers)
    print(f"AI analyze closed: {r19.status_code} {r19.text[:200]}")

# Test 20: AI workflow on closed ticket
if tid:
    print("\n=== TEST 20: AI workflow on closed ticket ===")
    r20 = client.post(f'/api/tickets/{tid}/ai/workflow', headers=agent_headers)
    print(f"AI workflow closed: {r20.status_code} {r20.text[:200]}")

# Test 21: Similar tickets on closed ticket
if tid:
    print("\n=== TEST 21: Similar tickets on closed ticket ===")
    r21 = client.get(f'/api/tickets/{tid}/similar', headers=agent_headers)
    print(f"Similar closed: {r21.status_code} {r21.text[:200]}")

# Cleanup
import os as os2
if os2.path.exists('e2e_full_test.db'):
    os2.remove('e2e_full_test.db')

print("\n=== E2E TEST COMPLETE ===")
