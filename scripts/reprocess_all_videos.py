import os, requests, time
ROOT='data/raw_videos'
base='http://127.0.0.1:8000'
if not os.path.exists(ROOT):
    print('raw_videos dir missing')
    raise SystemExit(1)
files=[f for f in os.listdir(ROOT) if os.path.getsize(os.path.join(ROOT,f))>0 and f.lower().endswith(('.mp4','.mov','.mkv'))]
if not files:
    print('no video files to process')
    raise SystemExit(0)

for f in files:
    path=os.path.join(ROOT,f)
    print('Uploading', f)
    try:
        with open(path,'rb') as fh:
            r=requests.post(f'{base}/api/upload_and_process', files={'file': (f, fh, 'video/mp4')}, timeout=600)
        print('status', r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print('upload failed for', f, e)
    # small pause between uploads
    time.sleep(2)
print('done')
