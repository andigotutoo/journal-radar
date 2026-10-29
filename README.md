# Paper Radar · 학술지 투고 레이더

교육학 KCI 학술지 투고 공고를 한 화면에서 확인하는 **공개 열람·소유자 편집** 웹사이트입니다.

## 이화여대 교육공학 연구자 게재 실적 TOP 50 선정 규칙

**목표 모집단:** KCI 학술지 검색의 **사회과학 → 교육학 → KCI 등재** 결과(사용자 확인 약 280종). 전체 목록은 아직 입력하지 않았으며, 280종이라는 숫자를 이미 수집한 것처럼 표시하지 않습니다.

1. 1순위: 논문 **저자별 소속기관**에 `이화여자대학교 교육공학과`가 명시된 논문의 학술지별 고유 논문 수.
2. 소속 학과를 판별할 자료가 없을 때: **소효정, 이정민, 임규연, 이재영, 정재삼, 조일현** 교수 6인의 확인된 KCI 게재 논문 수 합계로 정렬. 이름과 **같은 저자에 연결된 이화여대 소속정보**가 있어야 자동 포함하며 이름만 같으면 집계하지 않습니다. 다른 기관 재직 당시 실적은 별도 신원검증 후 수동 보완할 수 있습니다.
3. 동일 논문에 교수 2명이 공동저술한 경우 **학술지 전체 건수는 1편**, 교수별 건수는 각각 1편으로 표시합니다.
4. 동점일 때는 교수 6인의 게재 실적 합계 → KCI IF → 이름순으로 정렬합니다. 자료가 완전한 경우 0편인 학술지는 KCI IF순으로 채워 총 50곳을 표시할 수 있습니다.
5. 미확인/일부 추출 데이터로는 **최종 TOP 50을 확정하지 않고** '예비 집계'로 표시합니다. 논문 심사에 투고한 건수가 아닌 **게재 논문 수**임을 명확히 표시합니다.
6. **교육공학연구, 교육정보미디어연구, ETI는 게재 실적 순위와 무관하게 사이트 상단에 고정**됩니다.

### 자료 준비 (2개 파일)

**A. KCI 교육학 등재 학술지 목록:** [KCI 학술지 검색](https://www.kci.go.kr/kciportal/po/search/poSereSearList.kci)에서 `사회과학 → 교육학 → KCI 등재`를 적용해 CSV로 저장합니다. `학술지명`, `발행기관명`, `KCI IF (2년)` 및 가능한 경우 `홈페이지`, `투고URL`을 포함합니다. 처음에 KCI 학술지 명단이 구축되어야 논문 실적을 해당 학술지에 매칭할 수 있습니다.

```bash
python scripts/import_kci_csv.py kci_education_280.csv
```

**B. 게재 논문-저자-소속 데이터:** KCI의 [데이터 제공 서비스](https://www.kci.go.kr/kciportal/po/openapi/openDataPackGuide.kci?datasetBean.dtstTyCd=00) 또는 [KCI OAI-PMH](https://www.kci.go.kr/kciportal/po/openapi/openDataOaiPmhView.kci)에서 학술지명, 논문 ID, 제목, 발행연도, 저자명, **해당 저자의 소속기관**을 가져옵니다. 주저자 정보만 있고 공동저자의 소속이 없다면 공동저자 실적을 안전하게 집계할 수 없으므로 각 저자별 소속이 포함된 자료가 중요합니다.

KCI의 `oai_kci` XML이 있다면 저자-소속을 보존한 표로 변환할 수 있습니다. 또는 같은 형식의 CSV를 직접 작성할 수 있습니다.

```bash
python scripts/extract_oai_xml.py kci_2026_01.xml -o kci_author_paired.csv
python scripts/rank_publications.py kci_author_paired.csv --from-year 2017 --to-year 2026
```

CSV 열 형식: `article_id,journal,title,year,doi,url,author,affiliation`. **한 행은 논문 1편의 저자 1명**이며, 공동저자라면 동일 논문 ID를 여러 행에 적습니다. 소속기관을 저자와 분리해 하나의 통합 문자열로 적으면 잘못된 귀속이 발생할 수 있습니다.

**완료 검증:** 해당 검색범위의 누락 없는 원저 목록, 저자·소속 검증, 동일 저널 매칭을 확인하고 나서만 `--complete` 옵션으로 공식 상위 50선으로 확정하세요. 부분 데이터에는 `--complete`를 사용하지 마세요.

```bash
python scripts/rank_publications.py kci_author_paired.csv --from-year 2017 --to-year 2026 --complete
```

> 현재 제공되는 첫 버전은 **실제 교수별 출판 건수 0건으로 검증 완료되었다는 뜻이 아니라, 아직 집계 데이터가 연결되지 않은 상태**입니다. 따라서 사이트는 순위를 임의로 만들지 않습니다. KCI의 역사적 저자 소속, 동명이인 및 저자명 변경 등은 수동 검토가 필요할 수 있습니다.

## 현재 구현된 기능

- 공개 정적 대시보드. GitHub 로그인 없이 누구나 열람할 수 있습니다.
- 우선순위 3종: 교육공학연구, 교육정보미디어연구, Educational Technology International (ETI).
- KCI IF(2025, 2년) 정렬, 학술지 검색, 2027 공고 필터, 마감 전 필터.
- **이화 교육공학 연구자 실적 TOP 50** 섹션: 데이터가 확보되면 실적순 정렬. 자료 미확보 시 순위 미산출 표시.
- 공식 학술지 홈페이지와 논문 투고 시스템을 별도 링크로 연결(확인한 URL만).
- 2027.06.30 발행 목표일까지 남은 기간.
- 공식 공고를 확인할 수 있는 링크와 과거 공고 3건 예시(실제 2026년 공고).
- Python 수집기 + GitHub Actions 예약 실행(매일 09:17 KST).
- 학회 공지 페이지에서 자동 수집에 실패하면 실패/미확인 상태 표시.
- KCI에서 교육학 학술지를 CSV로 내려받아 추가할 수 있는 가져오기 스크립트.

## 가장 간단한 게시 방법 (15분 내외 — 안내 단계, 실제 소요시간 보장 아님)

1. GitHub 계정에서 **새 저장소 `journal-radar`**를 **Public**으로 만듭니다. README 초기화는 생략해도 됩니다.
2. ZIP의 내용을 압축 해제해 루트까지 모두 업로드합니다. `.github/workflows/publish.yml` **숨김 디렉터리**가 누락되지 않도록 주의하세요. GitHub 업로드 화면에서 `.github` 폴더가 안 올라가면 `git`으로 업로드하세요.
3. `Settings → Pages → Build and deployment → Source`에서 **GitHub Actions**를 선택합니다.
4. `Actions`에서 **Scan journals and publish website → Run workflow**를 실행합니다. 기본 브랜치는 `main`이어야 합니다.
5. 배포 성공 후 사이트 주소는 보통 `https://<GitHub아이디>.github.io/journal-radar/`입니다. 실제 주소는 `Settings → Pages`에서 확인하세요.
6. 동기들에게 **사이트 주소만 공유**하세요. GitHub 저장소에 동기를 Collaborator로 추가할 필요가 없습니다.

이 방식은 **모든 인터넷 사용자에게 공개**입니다. 링크를 아는 사람만 열어보도록 하는 접근통제 기능은 GitHub Free 공개 Pages에는 없습니다.

## 열람·편집 권한

- 동기: 사이트 읽기 전용. 사이트에 편집 화면이나 쓰기 API가 없습니다.
- 관리자: 저장소 소유자. GitHub 계정의 2단계 인증(2FA)을 권장합니다.
- GitHub 저장소가 Public이라 누구나 파일을 내려받고 복제(fork)할 수 있지만, 저장소의 실제 콘텐츠를 직접 수정·배포할 수는 없습니다. 변경 제안(PR)은 소유자가 허용·병합해야 합니다.
- 저장소에 개인정보, 학술지 관리자 계정, API 서비스키를 저장하지 마세요. 나중에 KCI API를 쓰는 경우 GitHub Actions Secrets를 이용하세요.

## 직접 수정하는 위치

| 파일 | 내용 |
| --- | --- |
| `site/index.html` | 페이지 구성 |
| `site/styles.css` | 디자인 |
| `site/app.js` | 필터·검색·상태 표시 |
| `site/data/journals.json` | 학술지 목록·IF·발행 간기·게시판 링크 |
| `site/data/notices.json` | 논문 모집 공고·마감일, 수동 확인 자료 |
| `site/data/ranking.json` | 소속·교수별 실적 순위, 근거 데이터의 완전성 |
| `scripts/rank_publications.py` | 논문별 저자·소속 자료를 토대로 순위 산출 |
| `scripts/extract_oai_xml.py` | KCI OAI-PMH XML의 저자-소속 정보를 CSV로 변환 |
| `scripts/scan.py` | 공식 공고 게시판에서 제목을 탐지하는 수집기 |
| `.github/workflows/publish.yml` | 자동 점검·사이트 배포 일정 |

## 학술지 전체 확대 방법

우선순위 3종만 기본 등록했습니다. **교육학 전체 201종이 이미 자동 등록되거나 감시되고 있는 것은 아닙니다.**

1. KCI 공식 인용정보에서 **교육학 분야** 필터를 선택하고 연도 2025로 조회합니다.
2. 학술지 목록을 CSV로 내보내거나 엑셀을 CSV UTF-8로 저장합니다.
3. 아래 명령으로 가져옵니다. CSV 헤더 예: `학술지명,발행기관명,KCI IF (2년),중분류`.

```bash
python scripts/import_kci_csv.py kci_education.csv
```

4. 추가된 학술지는 검색·IF 정렬에 표시되지만, **각 학회 공고 자동 감시 기능은 별도로 추가**해야 합니다. 공식 게시판 링크, 접근 가능 여부, 사이트별 파서 설정이 필요합니다. 추가 등록 학술지의 `monitoring`은 `unconfigured`로 표시됩니다.
5. KCI 공공데이터 학술지정보 API를 사용하여 목록 동기화를 확장할 수 있습니다. API 활용 신청과 서비스키 관리가 필요하며, **공고 마감일을 제공하는 API는 아닙니다.**

## 자동수집의 정확성 및 한계

- 첫 버전 수집기는 **한국교육공학회 공지사항**과 **한국교육정보미디어학회 JAMS 공지사항**을 확인합니다.
- 공고 목록의 HTML 구조가 바뀌거나 JavaScript가 필요한 경우 공고를 읽지 못할 수 있습니다. GitHub Actions 로그와 대시보드 점검 결과를 확인해야 합니다.
- 표기된 투고 마감일은 오직 원문에 연도가 명확히 나타나는 경우만 추출하며, 자동 파싱한 날짜는 보수적으로 **원문 재확인**으로 표시합니다. 2027년 접수일은 2026년 패턴에서 추측하지 않습니다.
- 사이트에 보이는 발행 간기는 정기적인 예정일입니다. 해당 호의 논문 심사 통과나 2027년 6월 내 게재가 보장되지 않습니다.
- GitHub Actions 예약 실행은 지연될 수 있고, 공개 저장소에서 활동이 60일 없으면 비활성화될 수 있으므로 Actions 페이지를 주기적으로 확인하세요.
- 수집기는 공개 게시판에만 접근하고, 로그인 우회나 차단 회피 기능을 포함하지 않습니다. 각 사이트의 이용조건·robots 정책을 확인하고 요청 빈도를 낮게 유지하세요.
- GitHub Pages는 읽기 전용 정적 공개 웹사이트입니다. 이메일 알림은 아직 구현하지 않았고, 추후 GitHub Issues, Gmail 또는 Telegram 등의 별도 알림 채널 연동이 가능합니다.

## 로컬 테스트

```bash
cd site
python -m http.server 8000
# 브라우저에서 http://localhost:8000
```

Python 수집기 실행: `pip install -r requirements.txt && python scripts/scan.py` (네트워크 접속 필요).

## 데이터 출처

- [한국교육공학회 공지사항](https://www.kset.or.kr/index.php?bo_idx=9&hCode=BOARD)
- [한국교육정보미디어학회 JAMS 공지사항](https://kaeim.jams.or.kr/co/com/EgovMenu.kci?s_MenuId=MENU-000000000061000&s_url=%2Fmobile%2Fpo%2Fcommunity%2Fnotice%2FnoticeList.kci)
- [KCI 학술지인용정보](https://www.kci.go.kr/)
- [KCI 학술지정보 공공데이터 API](https://www.data.go.kr/data/15085388/openapi.do)

2025년 2년 KCI IF: 교육공학연구 5.35, 교육정보미디어연구 4.31, ETI 0.16. 모두 KCI 공식 페이지에서 대조했습니다.

## 정합성 테스트

```bash
python scripts/test_scan.py
python scripts/test_ranking.py
python scripts/test_oai.py
```
