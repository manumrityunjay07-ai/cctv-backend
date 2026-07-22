import sqlite3
import os

db = os.path.join('data', 'events.db')
if not os.path.exists(db):
    print('events.db not found at', db)
    raise SystemExit(1)
conn = sqlite3.connect(db)
c = conn.cursor()
print('Schema before:')
c.execute("PRAGMA table_info(events);")
cols = [r[1] for r in c.fetchall()]
print(cols)
if 'snapshot' in cols:
    print('snapshot column already present')
else:
    try:
        c.execute('ALTER TABLE events ADD COLUMN snapshot TEXT')
        conn.commit()
        print('snapshot column added')
    except Exception as e:
        print('ALTER TABLE failed:', e)
print('Schema after:')
c.execute("PRAGMA table_info(events);")
print([r[1] for r in c.fetchall()])
conn.close()
