from scan import parse_kset, parse_kaeim, deadline_from_explicit_date

def test_kset():
    html = '''<table><tr><td>4</td><td><a href="/index.php?bo_idx=9&hCode=BOARD&idx=812&page=view">[교육공학연구] 제43권 1호 논문 모집 안내</a></td><td>2027-01-15</td></tr><tr><td><a href="/index.php?idx=81">학술대회 발표 논문 모집</a></td></tr></table>'''
    rows=parse_kset(html)
    assert len(rows)==1,rows
    assert rows[0]['journal_id']=='jet'
    assert rows[0]['published']=='2027-01-15'
    assert rows[0]['deadline'] is None

def test_kaeim():
    html = '''<table><tr><td><a href="javascript:void(0)" onclick="go('notiSeq=000000054579')">[교육정보미디어연구] 제33권 1호 논문 접수를 진행합니다</a></td><td>2026-12-28</td></tr></table>'''
    rows=parse_kaeim(html)
    assert len(rows)==1,rows
    assert 'notiSeq=000000054579' in rows[0]['url']

def test_deadline():
    assert deadline_from_explicit_date('논문 투고 마감: 2027년 2월 1일') == '2027-02-01'
    assert deadline_from_explicit_date('논문 모집 1월 31일까지') is None

if __name__=='__main__':
    test_kset();test_kaeim();test_deadline();print('3 parser tests passed')
