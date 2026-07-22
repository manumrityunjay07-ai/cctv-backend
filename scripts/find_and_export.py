import os, sqlite3, requests, time

DB = os.path.join('data','events.db')
if not os.path.exists(DB):
    print('events.db missing')
    raise SystemExit(1)

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT DISTINCT person_id FROM events WHERE person_id IS NOT NULL ORDER BY person_id")
pids = [r[0] for r in c.fetchall()]
conn.close()

base='http://127.0.0.1:8000'

for pid in pids:
    print('\nChecking', pid)
    try:
        r = requests.get(f'{base}/api/person_timeline', params={'person_id': pid}, timeout=30)
    except Exception as e:
        print('timeline request failed:', e)
        continue
    if r.status_code != 200:
        print('timeline status', r.status_code, r.text)
        continue
    j = r.json()
    items = j.get('items') or []
    print('events in timeline:', len(items))
    snaps = [it for it in items if it.get('snapshot')]
    print('events with snapshot:', len(snaps))
    if len(snaps) > 0:
        print('Attempting async export for', pid)
        try:
            r2 = requests.post(f'{base}/api/export_person_crops_async', params={'person_id': pid}, timeout=10)
        except Exception as e:
            print('export request failed:', e)
            raise SystemExit(1)
        print('export start status', r2.status_code)
        try:
            job = r2.json()
        except Exception:
            print('export start response:', r2.text)
            raise SystemExit(1)
        if not job.get('ok') or 'job_id' not in job:
            print('no job_id returned:', job)
            raise SystemExit(1)
        job_id = job['job_id']
        print('job_id', job_id)
        for i in range(80):
            try:
                s = requests.get(f'{base}/api/job_status', params={'job_id': job_id}, timeout=10).json()
            except Exception as e:
                print('status fetch failed:', e)
                break
            if s.get('ok') and 'job' in s:
                status = s['job'].get('status')
                print(i, status)
                if status in ('done','failed'):
                    print('final result:', s['job'].get('result'))
                    raise SystemExit(0)
            else:
                print(i, s)
            time.sleep(2)
        print('timed out polling job')
        raise SystemExit(1)

print('no persons with snapshots found')
