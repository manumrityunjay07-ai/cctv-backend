import os, sqlite3, requests, time

db = os.path.join('data','events.db')
if not os.path.exists(db):
    print('events.db not found')
    raise SystemExit(1)
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT DISTINCT person_id FROM events WHERE person_id IS NOT NULL ORDER BY person_id")
rows = [r[0] for r in c.fetchall()]
conn.close()
if not rows:
    print('no person_id found')
    raise SystemExit(1)

base = 'http://127.0.0.1:8000'

for pid in rows:
    print('\nTrying person_id:', pid)
    # start async export (no face_only)
    try:
        resp = requests.post(f'{base}/api/export_person_crops_async', params={'person_id': pid})
    except Exception as e:
        print('request failed:', e)
        continue
    print('start status', resp.status_code)
    try:
        job = resp.json()
    except Exception:
        print('start response:', resp.text)
        continue
    if not job.get('ok') or 'job_id' not in job:
        print('no job_id returned:', job)
        continue
    job_id = job['job_id']
    print('job_id', job_id)

    # poll
    for i in range(60):
        try:
            r = requests.get(f'{base}/api/job_status', params={'job_id': job_id})
            s = r.json()
        except Exception as e:
            print('status fetch failed:', e)
            break
        jobinfo = s.get('job') if s.get('ok') else None
        status = jobinfo.get('status') if jobinfo else s
        print(i, status)
        if jobinfo and jobinfo.get('status') in ('done','failed'):
            res = jobinfo.get('result')
            print('result:', res)
            if res and res.get('ok'):
                print('SUCCESS: person', pid, 'zip_url:', res.get('zip_url'))
                raise SystemExit(0)
            else:
                print('failed for person', pid, 'reason:', res)
            break
        time.sleep(2)
else:
    print('No successful exports found')
