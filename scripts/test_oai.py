from pathlib import Path
from tempfile import TemporaryDirectory
from extract_oai_xml import extract_file
sample='''<?xml version="1.0" encoding="utf-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
 <GetRecord><record><header><identifier>oai:kci.go.kr:ARTI/123</identifier></header>
 <metadata><oai_kci xmlns="http://www.kci.go.kr">
  <journalInfo><journal-name>교육공학연구</journal-name><pub-year>2026</pub-year></journalInfo>
  <articleInfo article-id="123"><title-group><article-title>테스트논문</article-title></title-group>
   <author-name><author><name>소효정</name><affiliation>이화여자대학교 교육공학과</affiliation></author>
   <author><name>임규연</name><affiliation>이화여자대학교 교육공학과</affiliation></author></author-name>
  </articleInfo></oai_kci></metadata></record></GetRecord></OAI-PMH>'''
with TemporaryDirectory() as t:
 p=Path(t)/'demo.xml';p.write_text(sample,'utf-8'); rows=extract_file(p)
 assert len(rows)==2 and rows[0]['journal']=='교육공학연구' and rows[1]['author']=='임규연'
print('KCI OAI-PMH 테스트 통과')
