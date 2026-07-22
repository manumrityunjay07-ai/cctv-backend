import sqlite3, os, requests, time

db = os.path.join('data','events.db')
if not os.path.exists(db):
    print('events.db not found')
    raise SystemExit(1)
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT DISTINCT person_id FROM events WHERE person_id IS NOT NULL ORDER BY person_id")
row = c.fetchone()
if not row:
    print('no person_id found in events table')
    raise SystemExit(1)
pid = row[0]
print('Selected person_id:', pid)

base = 'http://127.0.0.1:8000'
# timeline
print('\nCalling /api/person_timeline')
resp = requests.get(f'{base}/api/person_timeline', params={'person_id': pid})
print('status', resp.status_code)
try:
    j = resp.json()
    print('timeline events:', len(j.get('events', [])))
    if j.get('events'):
        print('first event snapshot:', j['events'][0].get('snapshot'))
except Exception as e:
    print('timeline response:', resp.text)

# best photo
print('\nCalling /api/best_photo')
resp = requests.get(f'{base}/api/best_photo', params={'person_id': pid})
print('status', resp.status_code)
try:
    j = resp.json()
    print('best_photo response keys:', list(j.keys()))
    if 'photo' in j:
        val = j['photo']
        print('best photo type:', type(val), 'len:' , (len(val) if hasattr(val, '__len__') else 'n/a'))
    if 'path' in j:
        print('best photo path:', j['path'])
except Exception:
    print('best_photo response:', resp.text)

# start async export
print('\nStarting async export via /api/export_person_crops_async')
resp = requests.post(f'{base}/api/export_person_crops_async', params={'person_id': pid, 'face_only': True})
print('status', resp.status_code)
job = None
try:
    job = resp.json()
    print('job:', job)
except Exception:
    print('export start response:', resp.text)

if not job or 'job_id' not in job:
    print('no job_id returned, abort')
    raise SystemExit(1)

job_id = job['job_id']
print('Polling job_status for job_id', job_id)
for i in range(60):
    resp = requests.get(f'{base}/api/job_status', params={'job_id': job_id})
    try:
        s = resp.json()
    except Exception:
        print('status response:', resp.text)
        break
    # API returns {'ok': True, 'job': {...}}
    if s.get('ok') and 'job' in s:
        status = s['job'].get('status')
        print(i, status)
        if status in ('done', 'failed'):
            print('final:', s)
            break
    else:
        print(i, s)
    time.sleep(3)
else:
    print('timed out waiting for job')

print('\nDone')
