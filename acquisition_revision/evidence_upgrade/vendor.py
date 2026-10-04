"""Credential-safe, auditable licensed-data collection, independent of parent inputs."""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime,timezone
from urllib.parse import urlparse

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from prepare import key,clean_url
import requests


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()


class Vendor:
    def __init__(self,root,offline=False):
        self.root=Path(root);self.cache=self.root/'cache';self.cache.mkdir(parents=True,exist_ok=True)
        self.offline=offline;self.session=requests.Session();self.receipts=[]
        if not offline:self.session.headers['Authorization']='Bearer '+key()

    def get(self,path,params=None,allow_not_found=False):
        url=path if path.startswith('https://') else 'https://api.massive.com'+path
        url=clean_url(requests.Request('GET',url,params=params).prepare().url)
        if urlparse(url).hostname!='api.massive.com':raise RuntimeError('Unexpected authenticated host')
        digest=hashlib.sha256(url.encode()).hexdigest();dest=self.cache/(digest+'.json')
        meta=self.cache/(digest+'.receipt.json')
        if dest.exists():
            data=json.loads(dest.read_text());receipt=json.loads(meta.read_text())
            if sha(dest)!=receipt['response_sha256']:raise RuntimeError('Response cache integrity failure')
            if receipt['http_status']==404 and not allow_not_found:raise RuntimeError('Vendor HTTP status 404')
        elif self.offline:raise RuntimeError('Missing independent raw response: '+path)
        else:
            from time import sleep
            response=None
            for attempt in range(4):
                try:
                    response=self.session.get(url,timeout=35)
                except requests.RequestException as error:
                    if attempt==3:raise RuntimeError('Vendor transport failed: '+type(error).__name__) from None
                    sleep(attempt+1);continue
                if response.status_code in (429,500,502,503,504):sleep(attempt+1);continue
                break
            missing=response is not None and response.status_code==404 and allow_not_found
            if response is None or (not response.ok and not missing):
                raise RuntimeError('Vendor HTTP status '+str(getattr(response,'status_code',None)))
            data=response.json()
            if not missing and data.get('status') not in ('OK','DELAYED'):raise RuntimeError('Vendor status failure')
            if data.get('next_url'):data['next_url']=clean_url(data['next_url'])
            dest.write_text(json.dumps(data,sort_keys=True))
            receipt={'url':url,'retrieved_utc':utc(),'response_sha256':sha(dest),
                     'response_file':dest.name,'http_status':response.status_code,'request_id':data.get('request_id')}
            meta.write_text(json.dumps(receipt,indent=2))
        self.receipts.append(receipt)
        return data

    def rows(self,path,params=None,max_pages=20):
        p=self.get(path,params);rows=list(p.get('results',[]))
        pages=1
        while p.get('next_url'):
            if pages>=max_pages:raise RuntimeError('Pagination exceeded explicit bound: '+path)
            p=self.get(p['next_url']);rows.extend(p.get('results',[]))
            pages+=1
        return rows
