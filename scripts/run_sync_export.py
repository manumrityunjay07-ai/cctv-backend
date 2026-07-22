import requests, os, time
base='http://127.0.0.1:8000'
pid='G-0001'
params={'person_id': pid, 'similarity_threshold': 0.78}
try:
    print('Calling /api/export_person_crops with params:', params)
    r = requests.get(f'{base}/api/export_person_crops', params=params, timeout=600)
    print('status', r.status_code)
    try:
        print('json:', r.json())
    except Exception:
        print('text:', r.text)
except Exception as e:
    print('request failed:', e)
