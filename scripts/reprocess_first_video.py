import requests, os
ROOT='data/raw_videos'
files = [f for f in os.listdir(ROOT) if os.path.getsize(os.path.join(ROOT,f))>0 and f.lower().endswith(('.mp4','.mov','.mkv'))]
if not files:
    print('no video files found')
    raise SystemExit(1)
fname = files[0]
path = os.path.join(ROOT,fname)
print('uploading', path)
url = 'http://127.0.0.1:8000/api/upload_and_process'
with open(path, 'rb') as fh:
    r = requests.post(url, files={'file': (fname, fh, 'video/mp4')})
    print('status', r.status_code)
    try:
        print(r.json())
    except Exception as e:
        print('response text:', r.text)
