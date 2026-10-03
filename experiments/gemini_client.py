"""Small REST client. Credentials go only to Google's API in a header."""
import json,urllib.request,urllib.error
from probe import ROOT

class GeminiError(RuntimeError):
    def __init__(self,code,status,retry_seconds=None):
        super().__init__(f'Gemini HTTP {code}: {status}')
        self.code=code;self.retry_seconds=retry_seconds

def request(path,payload=None):
    key=json.loads((ROOT.parent/'.secrets'/'gemini.json').read_text())['GEMINI_API_KEY']
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/'+path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'x-goog-api-key':key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not print request headers or raw error messages, which can contain credential details.
        try:
            error=json.loads(exc.read()).get('error',{});status=error.get('status','UNKNOWN')
            delay=next((x.get('retryDelay') for x in error.get('details',[]) if x.get('@type','').endswith('RetryInfo')),None)
            delay=float(delay.rstrip('s')) if delay else None
        except Exception:status='UNKNOWN';delay=None
        raise GeminiError(exc.code,status,delay) from None

if __name__=='__main__':
    data=request('models')
    models=[m['name'] for m in data.get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[])]
    preferred=['models/gemini-3.5-flash-lite','models/gemini-3.1-flash-lite','models/gemini-2.5-flash-lite']
    selected=next((m for m in preferred if m in models),None)
    if not selected:raise SystemExit('No configured Flash-Lite model available; stop before paid inference.')
    out={'credential_status':'valid_for_model_listing','selected_model':selected,'available_model_count':len(models)}
    (ROOT/'results'/'gemini_status.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out))
