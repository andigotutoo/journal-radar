#!/usr/bin/env python3
"""KCI 186종 보완: KCI 공개페이지+검색엔진 공개 인덱스로 후보 찾아 교차검증.
확인 불가능/동명이학술지/HTTP 차단 시 수정하지 않고 보고서 기록.
실행: pip install requests beautifulsoup4 ; python scripts/enrich_kci.py
"""
import json,re,time,sys,os,datetime,html
from pathlib import Path
from urllib.parse import quote,parse_qs,urlparse
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'site/data/journals.json'
REPORT=ROOT/'site/data/kci_enrichment_report.json'
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; PaperRadar/1.0; public-academic-data-check)'})
TIMEOUT=15
SERE=re.compile(r'(?:sere_id|sereId)=([\w\d]+)',re.I)
DATE=re.compile(r'(?<!\d)(0?[1-9]|1[0-2])\s*월\s*(0?[1-9]|[12]\d|3[01])\s*일')
def get(url):
 try:
  r=S.get(url,timeout=TIMEOUT);r.raise_for_status();r.encoding=r.apparent_encoding if r.encoding is None else r.encoding
  return r.text
 except Exception:return None
def discover(j):
 # 기존 식별번호 우선. 나머지는 Bing 공개 검색 결과에서 제목+발행기관 비교
 old=j.get('kci_sere_id') or (SERE.search(j.get('kci_url','')) or [None,None])[1]
 if old:return [old]
 query='site:kci.go.kr/kciportal/landing/journalHome.kci "'+j['name']+'"'
 u='https://www.bing.com/search?q='+quote(query)+'&count=7'
 page=get(u)
 if not page:return []
 soup=BeautifulSoup(page,'html.parser');found=[]
 for a in soup.find_all('a',href=True):
  href=html.unescape(a['href']); match=SERE.search(href)
  if match and 'journalHome.kci' in href and match.group(1) not in found:found.append(match.group(1))
 return found[:5]
def exact_name_matches(text,name):
 # HTML 메타 등 다른 이름의 포함 매치를 방지하기 위해 페이지 h1/h2/h3 텍스트 우선
 soup=BeautifulSoup(text,'html.parser')
 for h in soup.find_all(['h1','h2','h3']):
  if re.sub(r'\s+','',h.get_text())==re.sub(r'\s+','',name):return True
 return False
def analyze(text,j):
 soup=BeautifulSoup(text,'html.parser');body=soup.get_text(' ',strip=True)
 if not exact_name_matches(text,j['name']):return None,'제목 불일치'
 # 발행기관은 KCI 원문에 있지만 원본 엑셀 약칭이 다른 경우도 있으므로, 위험하면 날짜 미반영
 pub=j.get('publisher','').replace(' ','')
 publisher_ok = (not pub) or (pub in body.replace(' ',''))
 m=re.search(r'발행간기\s*(.{0,160}?)(?:ISSN|발행연도|KCI IF|저작권|발행기관)',body)
 block=m.group(1) if m else ''
 dates=sorted(set(f'{int(a):02d}-{int(b):02d}' for a,b in DATE.findall(block)))
 return (dates,publisher_ok),None
entries=json.loads(DB.read_text());report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total':len(entries),'verified_dates':0,'verified_kci_id':0,'updated':0,'unresolved':[]}
for i,j in enumerate(entries):
 if not j.get('kci_sere_id') or not j.get('publication_schedule'):
  ids=discover(j); hit=False; reasons=[]
  for sid in ids:
   url=f'https://www.kci.go.kr/kciportal/landing/journalHome.kci?sere_id={sid}'
   page=get(url)
   if not page:reasons.append('KCI 응답 실패');continue
   result,error=analyze(page,j)
   if error:reasons.append(error);continue
   dates,publisher_ok=result
   if not publisher_ok:reasons.append('발행기관 불일치');continue
   j.update(kci_sere_id=sid,kci_url=url,kci_detail_status='verified');hit=True
   if dates:
    j.update(publication_schedule=dates,publication_schedule_source=url,publication_schedule_status='published_rule')
   break
  if not hit:report['unresolved'].append({'name':j['name'],'reason':' / '.join(reasons) or 'KCI 후보 페이지 발견 실패'})
  elif j.get('publication_schedule'):report['updated']+=1
  if (i+1)%20==0:print('checked',i+1,'/',len(entries),flush=True)
  time.sleep(0.3)
 if j.get('publication_schedule') and j.get('publication_schedule_status')=='published_rule':report['verified_dates']+=1
 if j.get('kci_sere_id'):report['verified_kci_id']+=1
DB.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Result:',json.dumps({k:v for k,v in report.items() if k!='unresolved'},ensure_ascii=False))
