import requests

BASE_URL = 'http://127.0.0.1:8000'

# 1. Login as Professor
prof_res = requests.post(f'{BASE_URL}/login', data={'username': 'professor', 'password': 'prof123'})
assert prof_res.status_code == 200, f'Prof login failed: {prof_res.text}'
prof_token = prof_res.json()['access_token']
headers_prof = {'Authorization': f'Bearer {prof_token}'}

# Check Professor's view (Section A only = 50 submissions)
res = requests.get(f'{BASE_URL}/faculty/submissions?page=1&page_size=20', headers=headers_prof)
assert res.status_code == 200, res.text
data = res.json()
print('Professor Scope Total (Section A):', data['metrics']['total_in_scope'])
print('Professor Filtered Total:', data['total'])
print('Professor Items on Page 1 (size 20):', len(data['items']))
print('Professor Total Pages:', data['total_pages'])
assert data['metrics']['total_in_scope'] == 50
assert data['total'] == 50
assert len(data['items']) == 20
assert data['total_pages'] == 3

# Check filtering by Assignment 1 for Professor (10 in Section A)
res_asgn = requests.get(f'{BASE_URL}/faculty/submissions?assignment_id=1&page=1&page_size=20', headers=headers_prof)
assert res_asgn.status_code == 200
data_asgn = res_asgn.json()
print('Professor Asgn 1 Scope:', data_asgn['metrics']['total_in_scope'], 'Filtered:', data_asgn['total'], 'items:', len(data_asgn['items']))
assert data_asgn['metrics']['total_in_scope'] == 10
assert data_asgn['total'] == 10
assert len(data_asgn['items']) == 10

# 2. Login as HOD (All Sections = 150 submissions)
hod_res = requests.post(f'{BASE_URL}/login', data={'username': 'hod', 'password': 'hod123'})
assert hod_res.status_code == 200
hod_token = hod_res.json()['access_token']
headers_hod = {'Authorization': f'Bearer {hod_token}'}

res_hod = requests.get(f'{BASE_URL}/faculty/submissions?page=1&page_size=20', headers=headers_hod)
assert res_hod.status_code == 200
data_hod = res_hod.json()
print('HOD Scope Total (All Sections):', data_hod['metrics']['total_in_scope'])
print('HOD Filtered Total:', data_hod['total'])
print('HOD Total Pages (page size 20):', data_hod['total_pages'])
assert data_hod['metrics']['total_in_scope'] == 150
assert data_hod['total'] == 150
assert data_hod['total_pages'] == 8

# Filter by Section B for HOD (50 submissions)
res_sec_b = requests.get(f'{BASE_URL}/faculty/submissions?section_id=2&page=1&page_size=20', headers=headers_hod)
assert res_sec_b.status_code == 200
data_sec_b = res_sec_b.json()
print('HOD Section B Scope Total:', data_sec_b['metrics']['total_in_scope'])
print('HOD Section B Filtered Total:', data_sec_b['total'])
assert data_sec_b['metrics']['total_in_scope'] == 50
assert data_sec_b['total'] == 50

# 3. Check Pending Identification count
unassigned_res = requests.get(f'{BASE_URL}/faculty/unassigned-count', headers=headers_prof)
assert unassigned_res.status_code == 200
print('Professor Pending Identification Count:', unassigned_res.json()['count'])
assert unassigned_res.json()['count'] == 0

print('ALL FACULTY REVIEW QUEUE & PAGINATION CHECKS PASSED!')
