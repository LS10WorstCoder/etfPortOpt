import requests

login = requests.post('http://localhost:8000/api/auth/login', json={
    'email': 'tedtester99@gmail.com',
    'password': 'TestPass123!'
})
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

portfolios = requests.get('http://localhost:8000/api/portfolios', headers=headers).json()
p = portfolios[0]
print(f'Using portfolio: {p["id"][:8]}...')

print('\n1st Analysis Call:')
r1 = requests.post(f'http://localhost:8000/api/portfolios/{p["id"]}/analyze', headers=headers)
print(f'Status: {r1.status_code}')
if r1.status_code == 200:
    print(f'Value: ${r1.json()["total_value"]:.2f}')

print('\n2nd Analysis Call (should be cached):')
r2 = requests.post(f'http://localhost:8000/api/portfolios/{p["id"]}/analyze', headers=headers)
print(f'Status: {r2.status_code}')
if r2.status_code == 200:
    print(f'Cached: {r2.json().get("cached", False)}')
else:
    print(f'Error: {r2.text[:500]}')
