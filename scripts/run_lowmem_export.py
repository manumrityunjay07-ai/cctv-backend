import requests
base='http://127.0.0.1:8000'
params={'person_id':'G-0001','similarity_threshold':0.6,'downscale':0.5,'step':6}
print('calling', params)
r=requests.get(f"{base}/api/export_person_crops", params=params, timeout=600)
print('status', r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)
