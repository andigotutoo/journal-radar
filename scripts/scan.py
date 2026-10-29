"""Collect *titles and verified dates only* from official journal notice boards.

This is a starter crawler: site layouts can change. Never infer a deadline from
past years or a periodic publication schedule. A failed request does not mean
that a journal has no call for papers.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[1] / "site" / "data"
KSET = "https://www.kset.or.kr/index.php?bo_idx=9&hCode=BOARD"
KAEIM = ("https://kaeim.jams.or.kr/co/com/EgovMenu.kci?"
         "s_MenuId=MENU-000000000061000&"
         "s_url=%2Fmobile%2Fpo%2Fcommunity%2Fnotice%2FnoticeList.kci")
HEADERS = {"User-Agent": "PaperRadar/0.1 (+educational research journal notices; personal project)", "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}


def compact(value: str) -> str:
    return " ".join(value.split())


def pub_date_from_row(row: str) -> str | None:
    m = re.search(r"(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})", row)
    if not m:
        return None
    try:
        return f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}"
    except ValueError:
        return None


def deadline_from_explicit_date(page_text: str) -> str | None:
    """Return date only when a full year occurs immediately near a deadline keyword."""
    for m in re.finditer(r"20\d{2}\s*[년.\-/]\s*\d{1,2}\s*[월.\-/]\s*\d{1,2}\s*일?", page_text):
        prefix = page_text[max(0, m.start()-48):m.start()]
        if not re.search(r"마감|투고|접수|제출", prefix):
            continue
        nums = re.findall(r"\d+", m.group())[:3]
        if len(nums) != 3:
            continue
        try:
            dt = datetime(int(nums[0]), int(nums[1]), int(nums[2]))
            return dt.date().isoformat()
        except ValueError:
            pass
    return None


def journal_from_title(title: str) -> str | None:
    if re.search(r"교육공학\s*연구", title):
        return "jet"
    if re.search(r"Educational\s+Technology\s+International|\bETI\b", title, re.I):
        return "eti"
    if "교육정보미디어연구" in title:
        return "kaeim"
    return None


def is_call(title: str) -> bool:
    return bool(re.search(r"논문.*(모집|투고|접수)|원고.*(모집|접수)|투고.*안내", title))


def stable_id(journal: str, title: str) -> str:
    norm = re.sub(r"\s+", "", title).lower()
    return journal + "-" + hashlib.sha256(norm.encode()).hexdigest()[:16]


def parse_kset(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for anchor in soup.find_all("a", href=True):
        title = compact(anchor.get_text(" ", strip=True))
        journal = journal_from_title(title)
        if journal not in ("jet", "eti") or not is_call(title):
            continue
        url = urljoin(KSET, anchor["href"])
        parts = urlsplit(url)
        if parts.hostname not in ("www.kset.or.kr", "kset.or.kr"):
            continue
        if not parse_qs(parts.query).get("idx"):
            continue
        parent = anchor.find_parent("tr") or anchor.parent
        published = pub_date_from_row(compact(parent.get_text(" ", strip=True))) if parent else None
        results.append({"id": stable_id(journal,title), "journal_id": journal, "title":title,
                        "published":published, "deadline":None, "publication_date":None,
                        "url":url, "source":"official", "deadline_verified":False})
    return unique(results)


def parse_kaeim(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for anchor in soup.find_all("a"):
        title = compact(anchor.get_text(" ",strip=True))
        if journal_from_title(title) != 'kaeim' or not is_call(title):
            continue
        href = anchor.get("href", "")
        onclick = anchor.get("onclick", "")
        whole = href+" "+onclick
        m = re.search(r"notiSeq[=,\s'\"]+(\d{8,})",whole)
        if m:
            url = "https://kaeim.jams.or.kr/co/com/EgovMenu.kci?notiSeq="+m[1]+"&s_MenuId=MENU-000000000061000&s_url=%2Fpo%2Fcommunity%2Fnotice%2FnoticeView.kci"
        elif href.startswith("/") and "noticeView" in href:
            url = urljoin("https://kaeim.jams.or.kr", href)
        else:
            # The public board sometimes uses JavaScript navigation. Link to
            # its authoritative board, not a made-up article URL.
            url = KAEIM
        parent=anchor.find_parent("tr") or anchor.parent
        published=pub_date_from_row(compact(parent.get_text(" ",strip=True))) if parent else None
        results.append({"id":stable_id("kaeim", title), "journal_id":"kaeim", "title":title,
                        "published":published,"deadline":None,"publication_date":None,
                        "url":url,"source":"official", "deadline_verified":False})
    return unique(results)


def unique(records):
    seen = set(); result = []
    for r in records:
        key=(r["journal_id"],re.sub(r"\s+","",r["title"]).lower())
        if key not in seen:
            seen.add(key);result.append(r)
    return result


def fetch(url: str, timeout=18) -> str:
    response = requests.get(url, timeout=timeout, headers=HEADERS)
    response.raise_for_status()
    return response.text


def enrich_kset_detail(items):
    for n in items[:20]:
        try:
            html=fetch(n['url'], timeout=12)
            text=compact(BeautifulSoup(html,'html.parser').get_text(' ',strip=True))
            d=deadline_from_explicit_date(text)
            if d:
                n['deadline']=d
                n['deadline_verified']=False  # parsing is tentative; user should review original
        except requests.RequestException:
            pass
    return items


def run():
    notices_path=BASE/'notices.json'
    existing=json.loads(notices_path.read_text(encoding='utf-8'))
    statuses=[]
    all_new=[]
    for source, url, parser in [("한국교육공학회 공지사항",KSET,parse_kset),("한국교육정보미디어학회 JAMS",KAEIM,parse_kaeim)]:
        try:
            found=parser(fetch(url))
            if source.startswith("한국교육공학회"):
                found=enrich_kset_detail(found)
            if found:
                statuses.append({"name":source,"status":"ok","message":f"모집 공고 {len(found)}건 탐지"})
                all_new.extend(found)
            else:
                statuses.append({"name":source,"status":"warning","message":"접속 성공·공고 항목 미탐지: HTML 구조 확인 필요"})
        except (requests.RequestException,ValueError) as e:
            statuses.append({"name":source,"status":"error","message":str(e)[:110]})
    # Merge by journal/title and preserve all manually verified dates.
    def norm(n):return (n['journal_id'],re.sub(r"\s+","",n['title']).lower())
    old={norm(n):n for n in existing}
    for candidate in all_new:
        key=norm(candidate)
        if key not in old:
            old[key]=candidate
        else:
            prior=old[key]
            for key2 in ('published','deadline','publication_date'):
                if prior.get(key2) is None and candidate.get(key2) is not None:
                    prior[key2]=candidate[key2]
    final=sorted(old.values(),key=lambda n:n.get('published') or '',reverse=True)[:400]
    notices_path.write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    status={"last_checked":datetime.now(timezone.utc).isoformat(timespec='seconds'),"sources":statuses,
            "coverage_note":"우선 3개 학술지 감시. 교육학 전체 목록은 별도 KCI 내보내기 파일을 가져와 확장합니다."}
    (BASE/'scan.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Journal notices: {len(final)} / Newly parsed: {len(all_new)}")
    for s in statuses: print(s['name'],s['status'],s['message'])

if __name__=='__main__':run()
