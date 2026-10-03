"""Interactive local-only credential entry. No network, no key values printed."""
import argparse, getpass, json, os
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('provider',choices=['gemini','webull','databento'])
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
folder=root/'.secrets'
folder.mkdir(mode=0o700,exist_ok=True)
os.chmod(folder,0o700)
path=folder/(args.provider+'.json')
if path.exists():
    if input('A local credential file exists. Replace it? [y/N] ').lower()!='y':
        raise SystemExit('Unchanged.')
fields={'gemini':['GEMINI_API_KEY'],'webull':['WEBULL_APP_KEY','WEBULL_APP_SECRET'],'databento':['DATABENTO_API_KEY']}[args.provider]
data={}
for field in fields:
    value=getpass.getpass(field+' (hidden input): ').strip()
    if not value: raise SystemExit('Empty input; no credentials saved.')
    data[field]=value
fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
with os.fdopen(fd,'w') as f: json.dump(data,f)
os.chmod(path,0o600)
print('Saved locally with owner-only permissions. No network calls made.')
