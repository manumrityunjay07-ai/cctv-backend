import requests
r=requests.get('http://127.0.0.1:8000/api/person_timeline', params={'person_id':'G-0001'})
print(r.status_code)
try:
    j=r.json()
    print('items:', len(j.get('items',[])))
    for it in j.get('items',[])[:20]:
        print(it.get('event_id'), it.get('snapshot'))
except Exception:
    print(r.text)
