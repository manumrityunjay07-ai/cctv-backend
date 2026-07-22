import os, sqlite3, requests, time

DB = os.path.join('data','events.db')
BASE = 'http://127.0.0.1:8000'
PERSON = 'G-0001'

if not os.path.exists(DB):
    print('events.db missing')
    raise SystemExit(1)

conn = sqlite3.connect(DB)
c = conn.cursor()
# fetch events with snapshots for PERSON
c.execute("SELECT id, snapshot FROM events WHERE person_id=?", (PERSON,))
rows = c.fetchall()
if not rows:
    print('no snapshots for', PERSON)
    conn.close()
    raise SystemExit(1)

print('Found', len(rows), 'snapshot events for', PERSON)
all_backup = {r[0]: r[1] for r in rows}

thresholds = [0.9,0.85,0.8,0.75,0.7,0.65,0.6,0.55,0.5,0.45,0.4]
downscales = [1.0,0.75,0.5,0.33]
steps = [1,3,6,10]

# helper to set only one snapshot
def keep_only(event_id):
    for eid in all_backup:
        val = all_backup[eid] if eid==event_id else None
        c.execute('UPDATE events SET snapshot=? WHERE id=?', (val, eid))
    conn.commit()

# restore all
def restore_all():
    for eid,val in all_backup.items():
        c.execute('UPDATE events SET snapshot=? WHERE id=?', (val, eid))
    conn.commit()

try:
    for eid, snap in rows:
        print('\n=== Trying snapshot', eid, snap)
        keep_only(eid)
        # try parameter grid
        for thr in thresholds:
            for ds in downscales:
                for stp in steps:
                    params = {'person_id': PERSON, 'similarity_threshold': thr, 'downscale': ds, 'step': stp}
                    print('Trying params:', params)
                    try:
                        r = requests.get(f"{BASE}/api/export_person_crops", params=params, timeout=300)
                    except Exception as e:
                        print('request failed:', e)
                        time.sleep(1)
                        continue
                    print('HTTP', r.status_code)
                    try:
                        j = r.json()
                    except Exception:
                        print('non-json response:', r.text[:1000])
                        time.sleep(0.5)
                        continue
                    if j.get('ok'):
                        print('SUCCESS with snapshot', eid, 'params', params)
                        print('result:', j)
                        raise SystemExit(0)
                    else:
                        reason = j.get('reason') or j.get('exception') or str(j)
                        print('no match:', reason)
                    # short sleep to avoid overloading
                    time.sleep(0.5)
        print('Exhausted params for snapshot', eid)

    print('No successful export found for any snapshot and parameter combination')
finally:
    restore_all()
    conn.close()
    print('Restored DB snapshots and closed connection')
