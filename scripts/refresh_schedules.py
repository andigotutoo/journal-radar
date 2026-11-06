"""Verify official KCI catalog and journal detail, committing ten results per invocation."""
import argparse
import calendar
from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import re
import unicodedata
from urllib.parse import urljoin
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA = Path(__file__).resolve().parents[1] / "site/data"
DATE = re.compile(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일")


def key(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())


def fetch(url, **params):
    response = requests.get(url, params=params, timeout=25)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def inspect(journal):
    name, publisher = journal["name"], journal["publisher"]
    search = "https://www.kci.go.kr/kciportal/po/search/poSereSearList.kci"
    params = {"poSearchBean.searType": "journal", "from": "searchFromJournal",
              "poSearchBean.conditionList": "SERE_NM", "poSearchBean.keywordList": name,
              "poSearchBean.startPg": "1"}
    listing = fetch(search, **params)
    candidates = {}
    for link in listing.select('a.subject[href*="ciSereInfoView.kci"]'):
        label = link.get_text(" ", strip=True)
        if key(label) != key(name) and not key(label.split("(")[0]) == key(name) and not key(label).startswith(key(name + (journal.get("name_en") or "NO_ALIAS"))):
            continue
        match = re.search(r"sereId=(\w+)", link["href"])
        if match:
            candidates[match[1]] = (urljoin(search, link["href"]), "등재" in link.parent.get_text(" ", strip=True))
    accredited = {sid: item for sid, item in candidates.items() if item[1]}
    if accredited and "등재" in journal.get("kci", ""):
        candidates = accredited
    matches = []
    for sid, (url, _) in candidates.items():
        result = detail(journal, sid, url)
        if "kci_sere_id" in result:
            matches.append(result)
    if len(matches) > 1 and journal.get("name_en"):
        english = key(journal["name_en"])
        same = [r for r in matches if key(r.get("official_english", "").split("(")[0]) == english]
        if len(same) == 1:
            matches = same
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return {"reason": "동명이거나 발행기관 약칭이 같은 복수의 KCI 상세페이지", "candidate_urls": [r["kci_url"] for r in matches]}
    return {"reason": "검색 결과의 상세페이지에서 학술지명·발행기관 일치 항목 미확인",
            "candidate_count": len(candidates)}


def detail(journal, sid, url):
    name, publisher = journal["name"], journal["publisher"]
    soup = fetch(url)
    fields = {key(label.get_text(strip=True)): label.parent for label in soup.select(".grid-info > strong")}
    pub_link = fields.get("발행기관")
    pub_link = pub_link.select_one("a.colorBlue") if pub_link else None
    official_publisher = pub_link.get_text(" ", strip=True) if pub_link else ""
    # KCI lists some university institutes with the university prefix in detail.
    prefix = key(official_publisher).removesuffix(key(publisher))
    publisher_matches = key(official_publisher) == key(publisher) or (
        key(official_publisher).endswith(key(publisher)) and prefix.endswith("대학교") and "연구" in publisher
    )
    if not soup.title or key(soup.title.get_text(strip=True)) != key(name) or not publisher_matches:
        return {"reason": "KCI 상세 학술지명 또는 발행기관 불일치", "candidate_url": url}
    field = fields.get("발행간기")
    value = field.get_text(" ", strip=True) if field else ""
    pairs = DATE.findall(value)
    dates = sorted({f"{int(m):02}-{int(d):02}" for m,d in pairs if 1 <= int(m) <= 12 and 1 <= int(d) <= calendar.monthrange(2000,int(m))[1]})
    count = re.search(r"연\s*(\d+)\s*회", value)
    result = {"kci_sere_id": sid, "kci_url": url, "kci_detail_status": "verified", "official_publisher": official_publisher, "official_rule": " ".join(value.split())}
    english = soup.select_one("span.eng")
    if english:
        result["official_english"] = english.get_text(" ", strip=True)
    homepage = fields.get("학술지홈페이지")
    if homepage:
        for link in homepage.select("a[href]"):
            href = link["href"].strip()
            if href.startswith("javascript:"):
                href = link.get_text(strip=True)
            if href.startswith(("http://", "https://")):
                result["kci_journal_homepage"] = href
                break
    if dates and len(dates) == len(pairs) and (not count or len(dates) == int(count[1])):
        result.update(publication_schedule=dates, publication_schedule_source=url, publication_schedule_status="published_rule")
    else:
        if len(dates) < len(pairs):
            result["reason"] = "KCI 발행 간기에 존재하지 않거나 중복된 날짜 표기: " + ", ".join(f"{m}월 {d}일" for m, d in pairs)
        elif not pairs:
            result["reason"] = "KCI 상세페이지가 정확한 월·일을 제공하지 않음: " + " ".join(value.split())
        else:
            result["reason"] = "KCI 상세페이지의 연간 발행 횟수와 기재한 월·일 수가 다름: " + " ".join(value.split())
    if result.get("reason") and name == "한국교육" and publisher == "한국교육개발원":
        source = "https://www.kedi.re.kr/khome/main/journal/infoThesisGuide.do"
        guide = " ".join(fetch(source).get_text(" ", strip=True).split())
        rule = re.search(r"발행일은 매년 ([^。.]*)로 한다", guide)
        if rule and DATE.findall(rule[1]) == [("4", "30"), ("8", "31"), ("12", "31")]:
            result.update(publication_schedule=["04-30","08-31","12-31"], publication_schedule_source=source,
                          publication_schedule_status="published_rule")
            result.pop("reason")
    if result.get("reason") and dates:
        result.update(publication_schedule=dates, publication_schedule_source=url,
                      publication_schedule_status="partial_rule", publication_schedule_note=result["reason"])
    return result


def apply(journal, result):
    if result.get("kci_journal_homepage") and not journal.get("home_url"):
        journal["home_url"] = result["kci_journal_homepage"]
    for field in ("kci_journal_homepage","kci_sere_id","kci_url","kci_detail_status","publication_schedule","publication_schedule_source","publication_schedule_status","publication_schedule_note"):
        if field in result:
            journal[field] = result[field]


def save(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--begin", action="store_true")
    args = parser.parse_args()
    db, report = DATA/"journals.json", DATA/"kci_enrichment_report.json"
    journals = json.loads(db.read_text())
    state = json.loads(report.read_text())
    if args.begin and not state.get("in_progress"):
        state = {"in_progress": True, "done_ids": [], "unresolved": [], "updated": 0}
    done = set(state["done_ids"])
    remaining = [j for j in journals if j["id"] not in done]
    def check(journal):
        try:
            return inspect(journal)
        except requests.RequestException as error:
            return {"reason": "KCI 연결 오류: " + type(error).__name__}

    batch = remaining[:10]
    with ThreadPoolExecutor(max_workers=3) as workers:
        results = list(workers.map(check, batch))
    if results and all(r.get("reason", "").startswith("KCI 연결 오류") for r in results):
        raise RuntimeError("KCI 연결 실패: 마지막 GitHub 저장 지점부터 재시도")
    for j, result in zip(batch, results):
        before = dict(j)
        apply(j, result)
        state["updated"] += int(before != j)
        if "reason" in result:
            state["unresolved"].append({"name": j["name"], "reason": result["reason"]})
        state["done_ids"].append(j["id"])
    state.update(in_progress=len(remaining)>10, checked=len(state["done_ids"]), total=len(journals),
                 checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 verified_dates=sum(j.get("publication_schedule_status")=="published_rule" and bool(j.get("publication_schedule")) for j in journals),
                 verified_kci_id=sum(bool(j.get("kci_sere_id")) for j in journals))
    save(db, journals)
    save(report, state)


if __name__ == "__main__":
    main()
