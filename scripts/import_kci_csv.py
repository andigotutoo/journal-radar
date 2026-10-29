"""Import a KCI Education-subject CSV (export it manually from KCI as CSV).

Original priority journals are never overwritten. Only actual metadata from
input is used; journals with no official notice board remain unmonitored.
"""
import csv
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'site'/'data'/'journals.json'

def field(row,*keys):
    for k in keys:
        if row.get(k) not in (None,''):return row[k].strip()
    return ''

def run(path):
    journals=json.loads(DATA.read_text(encoding='utf-8'))
    byname={j['name']:j for j in journals}
    raw=Path(path).read_bytes()
    contents=None
    for encoding in ('utf-8-sig','cp949','euc-kr'):
        try:contents=raw.decode(encoding);break
        except UnicodeDecodeError:pass
    if contents is None:raise ValueError('UTF-8 / CP949 CSV만 지원합니다.')
    rows=csv.DictReader(contents.splitlines())
    added=0
    for row in rows:
        subject=field(row,'중분류','연구분야','주제분야')
        if subject and '교육학' not in subject:continue
        name=field(row,'학술지명','학술지 명','학술지','학회지명','Journal')
        if not name or name in byname:continue
        ifv=field(row,'KCI IF (2년)','IF(2년)','KCI IF','IF')
        try:ifvalue=float(re.sub(r'[^\d.]','',ifv)) if ifv not in ('','-') else None
        except ValueError:ifvalue=None
        publisher=field(row,'발행기관명','발행기관','발행 학회')
        item={'id':f'kci-{len(journals)+1:04d}','name':name,'name_en':'','publisher':publisher,'priority':0,
              'kci':field(row,'등재구분','등재정보') or '원문 확인', 'kci_if':ifvalue,
              'if_year':2025 if ifvalue is not None else None,
              'kci_url':field(row,'KCI 학술지 URL','KCI URL','KCI링크') or 'https://www.kci.go.kr',
              'home_url':field(row,'학술지홈페이지','학술지 홈페이지','학회 홈페이지','홈페이지','홈페이지URL','URL'),
              'submit_url':field(row,'논문투고URL','투고 시스템','투고URL','JAMS URL'),
              'site_url':field(row,'모집공고URL','공지사항URL','학회 공지사항'),
              'frequency':'','publication_schedule':[],'monitoring':'unconfigured',
              'fit':'','language':''}
        journals.append(item);byname[name]=item;added+=1
    DATA.write_text(json.dumps(journals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{added}종 추가 / 총 {len(journals)}종. 자동 공고 감시는 별도 주소 등록 필요.')

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('사용법: python scripts/import_kci_csv.py kci_education.csv')
    run(sys.argv[1])
