#!/usr/bin/env python3
"""Rank KCI education journals from verifiable, author-affiliation paired article records.

Input: UTF-8/CP949 CSV with at least:
  article_id, journal, title, year, author, affiliation
One row per article-author pair. Repeat an article ID for coauthors.
Other supported headers (Korean) described in README.

Rules:
- Primary: an AUTHOR whose affiliation identifies Ewha Educational Technology.
- Fallback: one of six named professors, whose individual affiliation is Ewha.
  A name without a paired Ewha affiliation is NOT matched automatically.
- Each article counts once per journal, even with multiple matching authors.
- Exact KCI journal roster restricts ranking when journal list is populated.
- Do not label partial article exports as complete rankings.
"""
import argparse
import csv
import io
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
DATA=BASE/'site'/'data'
FACULTY=['소효정','이정민','임규연','이재영','정재삼','조일현']
NAME_HEADERS=('author','author_name','저자','저자명','저자 이름','성명')
AFF_HEADERS=('affiliation','author_affiliation','소속','저자소속','저자 소속','저자소속기관')
JOURNAL_HEADERS=('journal','journal_name','학술지명','학술지','저널')
ID_HEADERS=('article_id','논문ID','논문 ID','논문번호','kci_id','KCI논문ID')
DOI_HEADERS=('doi','DOI')
TITLE_HEADERS=('title','논문명','논문제목','논문 제목','제목')
YEAR_HEADERS=('year','발행연도','발행년도','발행년','출판년도')
URL_HEADERS=('url','article_url','논문링크','원문링크')


def read_csv(path):
    blob=Path(path).read_bytes()
    for enc in ('utf-8-sig','cp949','euc-kr'):
        try:return list(csv.DictReader(io.StringIO(blob.decode(enc))))
        except UnicodeDecodeError:continue
    raise ValueError('UTF-8 / CP949 CSV로 저장해주세요.')


def get(row, keys):
    for k in keys:
        val=row.get(k)
        if val is not None and str(val).strip():return str(val).strip()
    return ''


def norm(s):
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',s or '')).lower()


def ewha(aff):
    a=norm(aff)
    return any(x in a for x in ('이화여자대학교','이화여대','ewhawomans','ewhawoman','ewhauniv'))


def dept(aff):
    a=norm(aff)
    return ewha(aff) and any(x in a for x in ('교육공학','educationaltechnology','instructionaltechnology','edtech'))


def faculty_name(author):
    a=norm(author)
    return next((p for p in FACULTY if a==norm(p)),None)


def valid_year(x):
    m=re.search(r'\b(?:19|20)\d{2}\b',x or '')
    return int(m.group()) if m else None


def count(rows,journals,complete=False,year_from=None,year_to=None):
    # Name matches are strict, no inferring any journal that is not in the roster.
    roster={norm(j['name']):j for j in journals}
    eligible={}
    uncertain=0
    for r in rows:
        journal=get(r,JOURNAL_HEADERS)
        obj=roster.get(norm(journal))
        if not obj:continue
        y=valid_year(get(r,YEAR_HEADERS))
        if year_from and (y is None or y<year_from):continue
        if year_to and (y is None or y>year_to):continue
        author=get(r,NAME_HEADERS)
        affiliation=get(r,AFF_HEADERS)
        prof=faculty_name(author)
        # Author+affiliation must be paired in this row.
        is_department=bool(dept(affiliation))
        is_faculty=bool(prof and ewha(affiliation))
        if prof and not ewha(affiliation):uncertain+=1
        if not (is_department or is_faculty):continue
        doi=get(r,DOI_HEADERS).lower().removeprefix('https://doi.org/').strip()
        id_val=get(r,ID_HEADERS)
        title=get(r,TITLE_HEADERS)
        # Require a dependable article identity so distinct articles are not merged.
        ident=('doi:'+doi if doi else 'kci:'+id_val if id_val else
               'title:'+norm(title)+':'+str(y or '') if title else '')
        if not ident:continue
        key=(obj['id'],ident)
        e=eligible.setdefault(key,{'journal_id':obj['id'],'doi':doi,'article_id':id_val,
                     'title':title,'year':y,'url':get(r,URL_HEADERS),
                     'department':False,'faculty':set()})
        e['department']=e['department'] or is_department
        if is_faculty:e['faculty'].add(prof)
        if not e['url']:e['url']=get(r,URL_HEADERS)
    sums=defaultdict(lambda:{'department_papers':0,'faculty_papers':0,'by_professor':{p:0 for p in FACULTY},'articles':[]})
    for article in eligible.values():
        cell=sums[article['journal_id']]
        if article['department']:cell['department_papers']+=1
        if article['faculty']:cell['faculty_papers']+=1
        for p in article['faculty']:cell['by_professor'][p]+=1
        cell['articles'].append({'title':article['title'],'year':article['year'],'url':article['url'],
                    'faculty':sorted(article['faculty']), 'department':article['department']})
    # Prefer department metric when it has verified records, otherwise use faculty metric.
    department_total=sum(v['department_papers'] for v in sums.values())
    faculty_total=sum(v['faculty_papers'] for v in sums.values())
    mode='department' if department_total else 'faculty' if faculty_total else 'unavailable'
    byid={j['id']:j for j in journals}
    ranked=[]
    journal_ids=[j['id'] for j in journals] if complete else list(sums.keys())
    for jid in journal_ids:
        v=sums[jid]
        score=v['department_papers'] if mode=='department' else v['faculty_papers']
        if not complete and not score:continue
        j=byid[jid]
        ranked.append({'journal_id':jid,'journal':j['name'],'score':score,
             'department_papers':v['department_papers'],'faculty_papers':v['faculty_papers'],
             'by_professor':v['by_professor'],
             'articles':sorted(v['articles'],key=lambda a:a['year'] or 0,reverse=True)})
    ranked.sort(key=lambda v:(-v['score'],-v['faculty_papers'],-(byid[v['journal_id']].get('kci_if') or 0),v['journal']))
    return {'mode':mode,
        'complete':complete,'year_from':year_from,'year_to':year_to,
        'faculty':FACULTY,'verified_journals':len(ranked),
        'verified_articles':len(eligible),'unverified_name_rows':uncertain,
        'ranked':ranked[:50], 'updated_at':str(date.today()),
        'note':('KCI 전체 자료 수집 완료 및 저자-소속 검증 후 산정' if complete else
                '일부 입력된 자료에 대한 예비 집계이며 전체 학술지 순위가 아님')}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('csv',help='논문-저자 한 행씩 구성된 KCI 자료 CSV')
    parser.add_argument('--complete',action='store_true',help='완전한 대상 범위 추출과 검증을 마친 경우에만 사용')
    parser.add_argument('--from-year',type=int)
    parser.add_argument('--to-year',type=int)
    args=parser.parse_args()
    journals=json.loads((DATA/'journals.json').read_text('utf-8'))
    out=count(read_csv(args.csv),journals,complete=args.complete,year_from=args.from_year,year_to=args.to_year)
    (DATA/'ranking.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f"집계 방식: {out['mode']}; 확인 논문: {out['verified_articles']}편; 게재지: {out['verified_journals']}종; 완전성: {out['complete']}")
    print('상위 50 선정은 전체 범위의 완전한 저자-소속 자료가 확보된 뒤에만 확정할 수 있습니다.')

if __name__=='__main__':main()
