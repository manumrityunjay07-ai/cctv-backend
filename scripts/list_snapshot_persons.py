import sqlite3
conn=sqlite3.connect('data/events.db')
c=conn.cursor()
c.execute("SELECT person_id, COUNT(*) FROM events WHERE snapshot IS NOT NULL GROUP BY person_id")
rows=c.fetchall()
print('persons with snapshot counts:')
for r in rows:
    print(r)
conn.close()
