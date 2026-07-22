import os, sqlite3, requests, time

DB = os.path.join('data','events.db')
if not os.path.exists(DB):
    print('events.db missing')
    raise SystemExit(1)

person_id = 'G-0001'
base = 'http://127.0.0.1:8000'

conn = sqlite3.connect(DB)
c = conn.cursor()
# fetch events with snapshots
c.execute("SELECT id, snapshot FROM events WHERE person_id=? AND snapshot IS NOT NULL", (person_id,))
rows = c.fetchall()
if not rows:
    print('no snapshots found for', person_id)
    conn.close()
    raise SystemExit(1)

print('found snapshots:', len(rows))
# choose first snapshot to keep
keep_id, keep_snap = rows[0]
print('keeping snapshot for event', keep_id, keep_snap)

# backup mapping
backup = {r[0]: r[1] for r in rows}

try:
    # set snapshot=NULL for all other events of this person
    for eid, snap in rows:
        if eid != keep_id:
            c.execute('UPDATE events SET snapshot=NULL WHERE id=?', (eid,))
    conn.commit()

    # trigger async export
    print('starting export_person_crops_async for', person_id)
    r = requests.post(f'{base}/api/export_person_crops_async', params={'person_id': person_id}, timeout=10)
    print('start status', r.status_code)
    try:
        job = r.json()
    except Exception:
        print('start response:', r.text)
        raise SystemExit(1)
    if not job.get('ok') or 'job_id' not in job:
        print('no job_id returned:', job)
        raise SystemExit(1)
    job_id = job['job_id']
    print('job_id', job_id)

    # poll job
    for i in range(120):
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
                break
        else:
            print(i, s)
        time.sleep(2)

finally:
    # restore backups
    for eid, snap in backup.items():
        c.execute('UPDATE events SET snapshot=? WHERE id=?', (snap, eid))
    conn.commit()
    conn.close()
    print('restored snapshots')
