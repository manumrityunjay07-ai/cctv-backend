import sqlite3, os
pid='G-0002'
db=os.path.join('data','events.db')
if not os.path.exists(db):
    print('events.db missing')
    raise SystemExit(1)
conn=sqlite3.connect(db)
c=conn.cursor()
try:
    c.execute("SELECT id, snapshot FROM events WHERE person_id=?", (pid,))
    rows=c.fetchall()
except Exception as e:
    print('query failed:', e)
    conn.close()
    raise
conn.close()
print('events for', pid, 'count=', len(rows))
for r in rows[:10]:
    print(r)

# list snapshot dir
snap_dir=os.path.join('data','snapshots')
print('\nSnapshots dir exists:', os.path.exists(snap_dir))
if os.path.exists(snap_dir):
    files=[f for f in os.listdir(snap_dir) if os.path.isfile(os.path.join(snap_dir,f))]
    print('snapshot files count:', len(files))
    print(files[:20])
else:
    print('no snapshot dir')
