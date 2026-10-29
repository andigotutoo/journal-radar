from rank_publications import count, FACULTY
journals=[{'id':'jet','name':'교육공학연구','kci_if':5.35}, {'id':'other','name':'교육방법연구','kci_if':2.06}]
rows=[
 {'article_id':'a1','journal':'교육공학연구','title':'A','year':'2025','author':'소효정','affiliation':'이화여자대학교 교육공학과'},
 {'article_id':'a1','journal':'교육공학연구','title':'A','year':'2025','author':'임규연','affiliation':'이화여자대학교 교육공학과'},
 {'article_id':'a2','journal':'교육방법연구','title':'B','year':'2024','author':'이재영','affiliation':'이화여자대학교 교육공학과'},
 {'article_id':'a3','journal':'교육공학연구','title':'C','year':'2024','author':'이정민','affiliation':'다른대학교'},
 {'article_id':'a4','journal':'교육공학연구','title':'D','year':'2025','author':'이정민','affiliation':'이화여자대학교 교육공학과'}]
res=count(rows,journals)
assert res['mode']=='department'
assert res['verified_articles']==3
assert res['ranked'][0]['score']==2
assert res['ranked'][0]['by_professor']['소효정']==1
assert res['ranked'][0]['by_professor']['임규연']==1
assert res['unverified_name_rows']==1
fallback=count([{'article_id':'a10','journal':'교육공학연구','year':'2024','author':'정재삼','affiliation':'이화여자대학교','title':'X'}],journals)
assert fallback['mode']=='faculty' and fallback['ranked'][0]['score']==1
assert len(FACULTY)==6
print('순위 집계 테스트 통과 (중복 제거, 교수별 집계, 소속 검증, fallback)')
