import unittest
from enrich_kci import analyze

class KciParserTests(unittest.TestCase):
 def page(self, dates, name='교육공학연구', publisher='한국교육공학회'):
  return f'<h2>{name}</h2><p>{publisher}</p><table><tr><th>발행간기</th><td>{dates}</td></tr></table><p>12월 01일</p>'
 def parse(self, text):
  return analyze(text, {'name':'교육공학연구','publisher':'한국교육공학회'})
 def test_only_schedule_dates(self):
  self.assertEqual(self.parse(self.page('06월 30일, 03월 31일, 03월 31일'))[0], (['03-31','06-30'], True))
 def test_impossible_date(self):
  self.assertEqual(self.parse(self.page('02월 31일, 04월 30일'))[0][0], ['04-30'])
 def test_wrong_journal(self):
  self.assertEqual(self.parse(self.page('03월 31일',name='다른 학술지'))[1], '제목 불일치')
 def test_wrong_publisher(self):
  self.assertFalse(self.parse(self.page('03월 31일',publisher='다른 기관'))[0][1])
 def test_frequency_is_not_an_exact_date(self):
  self.assertEqual(self.parse(self.page('연4회'))[0][0], [])

if __name__=='__main__':
 unittest.main()
