const state={journals:[],notices:[],scan:{},noticeFilter:'all',showAllNotices:false,showAllRankings:false,query:'',sort:'ranking',onlyPriority:false,ranking:{mode:'unavailable',complete:false,ranked:[]}};
const el=id=>document.getElementById(id);
const dateOnly=(s)=>s?new Date(`${s}T00:00:00+09:00`):null;
const pretty=(s)=>s?(s.replace(/-/g,'.')):'공고 원문 확인';
function make(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function link(url,label,cls){const a=make('a',cls,label);if(url && /^https:\/\//i.test(url)){a.href=url;a.target='_blank';a.rel='noopener noreferrer';}else{a.href='#';a.setAttribute('aria-disabled','true');}return a;}
function journalLinks(j,cls=''){const out=[];if(j.submit_url)out.push(link(j.submit_url,'투고 ↗',cls));if(j.home_url||j.site_url)out.push(link(j.home_url||j.site_url,'학회 홈페이지 ↗',cls));else if(j.kci_url)out.push(link(j.kci_url,'KCI에서 확인 ↗',cls));return out;}
function humanStatus(n){const now=new Date();const d=dateOnly(n.deadline);if(!d)return{label:'마감일 미확인',css:'pending'};if(d.getTime()+86400000>now.getTime())return{label:'마감 전 · 원문 확인',css:'open'};return{label:'지난 공고',css:'old'};}
function goal(){const today=new Date();const end=dateOnly('2027-06-30');const left=Math.ceil((end-today)/86400000);el('days-left').textContent=Math.abs(left).toLocaleString()+'일';el('days-label').textContent=left>=0?'발행 목표일까지 남음':'발행 목표일 경과';}
function setMetrics(){el('journal-count').textContent=state.journals.length.toLocaleString()+'종';el('priority-count').textContent=state.journals.filter(j=>j.priority>0).length+'종';el('notice-count').textContent=state.notices.length+'건';let d=state.scan.last_checked;el('last-check').textContent=d?new Date(d).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'미실행';const sources=state.scan.sources||[];el('scan-summary').textContent=sources.filter(x=>x.status==='ok').length+'개 출처 점검 성공';}
function exactDates(j){if(j.publication_schedule_status==='published_rule' && (j.publication_schedule||[]).length)return j.publication_schedule.map(x=>x.replace('-','월 ')+'일').join(' · ');return '정확한 발행일 확인 전';}
function scoreFor(j){const rec=(state.ranking.ranked||[]).find(r=>r.journal_id===j.id);return rec?rec.score:null;}
function renderRanking(){
 const wrap=el('ranking-list');wrap.replaceChildren();
 const r=state.ranking;
 const mode=r.mode==='department'?'이화여대 교육공학과 소속 저자':r.mode==='faculty'?'지정 교수 6명':'저자-소속 자료 미확보';
 el('ranking-status').textContent=(r.complete?'검증 집계':'예비 집계')+' · '+mode+' · '+(r.verified_articles||0)+'편 확인';
 const ranked=r.ranked||[];
 if(!ranked.length){
   wrap.append(make('div','empty','아직 교수별 게재 실적 자료가 없습니다. 순위를 등록하면 투고 일정과 함께 표시됩니다.'));
   el('expand-rankings').hidden=true;return;
 }
 const noticeByJournal=new Map(visibleNotices().map(n=>[n.journal_id,n]));
 const limit=state.showAllRankings?ranked.length:Math.min(10,ranked.length);
 ranked.slice(0,limit).forEach((item,i)=>{
  const journal=state.journals.find(j=>j.id===item.journal_id);
  if(!journal)return;
  const line=make('article','merged-ranking-row');
  line.append(make('div','rank-no',String(i+1).padStart(2,'0')));
  const details=make('div','rank-details');details.append(make('strong','',journal.name),make('p','',journal.publisher||''));details.append(make('small','',`정기 발행일: ${exactDates(journal)} · ${journal.frequency||'주기 미확인'}`));
  const profs=Object.entries(item.by_professor||{}).filter(([,n])=>n>0).map(([k,n])=>`${k} ${n}`).join(' · ');
  if(profs)details.append(make('small','',profs));line.append(details);
  line.append(make('div','rank-score',String(item.score)+'편'));
  const notice=noticeByJournal.get(journal.id);
  const due=make('div','merge-date');
  const pub=make('div','merge-date');
  if(notice){
   due.append(make('strong','',pretty(notice.deadline)),make('small',notice.displayYear==='2027'?'2027년 공고':'2026년 참고'));
   pub.append(make('strong','',notice.publication_date?pretty(notice.publication_date):'해당 호 미확인'));if(!notice.publication_date)pub.append(make('small','',`정기 발행: ${exactDates(journal)}`));
  }else{const rules=journal.submission_deadline_status==='official_rule'?(journal.submission_deadline_rules||[]):[];due.append(make('span','merge-unknown',rules.length?'정기 마감: '+rules[0].replace('-','월 ')+'일':'공고 미확인'));if(rules.length)due.append(make('small','',`2027년 공고 미확인 · 공식 규정`));pub.append(make('small','',`정기 발행: ${exactDates(journal)}`));}
  line.append(due,pub);
  const links=make('div','merge-links');
  if(notice&&notice.url)links.append(link(notice.url,'공고 ↗'));
  journalLinks(journal).forEach(a=>links.append(a));
  if(journal.kci_url){const detail=/[?&]sereId=/.test(journal.kci_url);links.append(link(journal.kci_url,detail?'KCI 상세정보 ↗':'KCI 학술지 검색 ↗'));}
  line.append(links);wrap.append(line);
 });
 const expand=el('expand-rankings');expand.hidden=ranked.length<=10;
 expand.textContent=state.showAllRankings?'접기':`전체 ${ranked.length}종 보기`;
 if(!r.complete&&!state.showAllRankings)wrap.prepend(make('div','ranking-warning','자료 일부를 기반으로 집계한 예비 순위입니다. 전체 KCI 게재 실적의 최종 순위가 아닙니다.'));
}
function renderPriority(){const wrap=el('priority-grid');wrap.replaceChildren();state.journals.filter(j=>j.priority>0).sort((a,b)=>a.priority-b.priority).forEach(j=>{const c=make('article','journal-card');const top=make('div','jc-top');top.append(make('span','rank',`★ PRIORITY 0${j.priority}`),make('span','mini-badge',j.kci+' · '+j.language));c.append(top,make('h3',j.name_en===j.name?'english':'',j.name),make('div','jc-publisher',j.publisher));const meta=make('div','jc-meta');[j.frequency,`정기 발행: ${exactDates(j)}`,j.fit].filter(Boolean).forEach(t=>meta.append(make('span','',t)));c.append(meta);const ft=make('div','jc-footer');const ifv=make('div','if','2025 KCI IF');ifv.append(make('strong','',j.kci_if==null?'—':Number(j.kci_if).toFixed(2)));ft.append(ifv,link(j.home_url||j.site_url,'학술지 홈페이지 ↗')); c.append(make('div','small-links',''));const sm=c.lastElementChild;sm.append(link(j.submit_url||j.site_url,'투고 시스템 ↗'),link(j.site_url,'모집 공고 ↗'));c.append(ft);wrap.append(c);});}
// 한 학술지당 2027년 상반기 최우선 공고 1건,
// 없으면 2026년 1~5월 투고 마감 중 가장 이른 공고 1건만 노출합니다.
function noticeDate(n){return /^20\d\d-\d\d-\d\d$/.test(n.deadline||'')?n.deadline:null;}
function noticeYear(n){
  const d=noticeDate(n);if(d)return Number(d.slice(0,4));
  // 투고일이 없는 경우 제목의 대상 연도만 인식. 게시 연도는 대체하지 않음.
  const y=(n.title||'').match(/20(26|27)년/);return y?Number(y[0].slice(0,4)):null;
}
function visibleNotices(){
 const groups=new Map();
 state.notices.forEach(n=>{if(!n.journal_id)return;const a=groups.get(n.journal_id)||[];a.push(n);groups.set(n.journal_id,a);});
 const picks=[];
 for(const [id,ns] of groups){
  const sortEarliest=(a,b)=>(noticeDate(a)||'9999-99-99').localeCompare(noticeDate(b)||'9999-99-99') || (b.published||'').localeCompare(a.published||'');
  // 반드시 투고일이 확인된 공고만 순위에 반영. 발행일이 2027-06-30 이후로
  // 확인된 경우에는 2027 졸업 기한 후보에서 제외합니다.
  const future=ns.filter(n=>{const d=noticeDate(n);return d&&d>='2027-01-01'&&d<='2027-06-30' && (!n.publication_date || n.publication_date<='2027-06-30');}).sort(sortEarliest);
  const past=ns.filter(n=>{const d=noticeDate(n);return d&&d>='2026-01-01'&&d<='2026-05-31';}).sort(sortEarliest);
  const chosen=future[0]||past[0];
  if(chosen)picks.push({...chosen,displayYear:future.length?'2027':'2026'});
 }
 return picks.sort((a,b)=> (a.displayYear===b.displayYear?0:a.displayYear==='2027'?-1:1) || (a.deadline||'').localeCompare(b.deadline||'') || (a.journal_id||'').localeCompare(b.journal_id||''));
}
function renderNotices(){
 const wrap=el('notice-list');wrap.replaceChildren();
 let arr=visibleNotices();
 if(state.noticeFilter==='new')arr=arr.filter(n=>n.displayYear==='2027');
 if(state.noticeFilter==='open')arr=arr.filter(n=>humanStatus(n).css==='open');
 if(!arr.length){wrap.append(make('div','empty',state.noticeFilter==='new'?'2027년 상반기 투고 공고는 아직 확인되지 않았습니다. 전체 공고에서 2026년 참고 일정을 확인할 수 있어요.':'해당 조건에서 검증된 투고 마감일을 가진 공고가 없습니다.'));return;}
 // 학술지별 최대 한 건만. 화면이 다시 과밀해지지 않도록 5건 기본 표시.
 const limit=state.showAllNotices?arr.length:5;
 arr.slice(0,limit).forEach(n=>{
  const j=state.journals.find(x=>x.id===n.journal_id);
  const row=make('article','notice-row');
  const main=make('div');main.append(make('span','tag',j?j.name:'학술지'));
  const h=make('h4');h.append(link(n.url,n.title));main.append(h);
  main.append(make('p','',n.displayYear==='2027'?'2027년 실제 공고':'2026년 참고 일정 · 2027년 공고 미확인'));
  const when=make('div');when.append(make('p','','투고 마감'),make('time','',pretty(n.deadline)));
  when.append(make('p','',`게재/발행 예정: ${n.publication_date?pretty(n.publication_date):'미확인 (공식 원문 확인)'}`));
  const sb=make('div','status-block');const status=humanStatus(n);
  sb.append(make('span',`tag ${status.css}`,status.label));
  const btn=make('div','');btn.style.marginTop='9px';btn.append(link(n.url,'공고 열기 ↗'));sb.append(btn);
  row.append(main,when,sb);wrap.append(row);
 });
 if(arr.length>5){
  const button=make('button','chip',state.showAllNotices?'접기':'전체 '+arr.length+'건 보기');
  button.type='button';button.style.margin='16px';button.addEventListener('click',()=>{state.showAllNotices=!state.showAllNotices;renderNotices();});wrap.append(button);
 }
}
function renderJournals(){const wrap=el('journal-list');wrap.replaceChildren();let arr=state.journals.filter(j=>{const q=state.query.toLowerCase();return (!state.onlyPriority||j.priority>0)&&(!q||[j.name,j.name_en,j.publisher,j.fit].join(' ').toLowerCase().includes(q));});const sort=state.sort;arr.sort((a,b)=>sort==='ranking'?((scoreFor(b)??-1)-(scoreFor(a)??-1))||((a.priority||999)-(b.priority||999)):sort==='if'?((b.kci_if??-1)-(a.kci_if??-1)):sort==='name'?a.name.localeCompare(b.name,'ko'):((a.priority||999)-(b.priority||999))||((b.kci_if??0)-(a.kci_if??0)));
 if(!arr.length){wrap.append(make('div','empty','검색 조건에 맞는 학술지가 없습니다.'));return;}
 arr.forEach(j=>{const row=make('article','journal-row');const h=make('div');h.append(make('h4','',j.name),make('p','',`${j.publisher} · 정기 발행: ${exactDates(j)} · ${j.language||''}`));const ifc=make('div','if-cell',j.kci_if!=null?Number(j.kci_if).toFixed(2):'—');const sc=scoreFor(j);const label=make('div','label-cell',sc!==null?sc+'편 게재':j.priority>0?'★ 우선 추적':'집계 전');const urls=make('div','links');journalLinks(j).forEach(a=>urls.append(a));if(j.kci_url&&(j.home_url||j.site_url))urls.append(link(j.kci_url,'KCI ↗'));row.append(h,ifc,label,urls);wrap.append(row);});}
function renderSources(){const dest=el('source-status');dest.replaceChildren();(state.scan.sources||[]).forEach(s=>{const r=make('div','source-line');r.append(make('strong',s.status==='ok'?'✓':s.status==='error'?'!':'○'));r.firstChild.className=s.status==='ok'?'ok':s.status==='error'?'error':'neutral';r.append(make('span','',s.name+' · '+(s.status==='ok'?'점검 성공':s.status==='error'?'점검 실패':s.message||'점검 전')));dest.append(r);});}
async function loadJSON(path){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw new Error(path+' HTTP '+r.status);return r.json();}
async function boot(){goal();try{const [journals,notices,scan,ranking]=await Promise.all(['./site/data/journals.json','./site/data/notices.json','./site/data/scan.json','./site/data/ranking.json'].map(loadJSON));state.journals=journals;state.notices=notices;state.scan=scan;state.ranking=ranking;setMetrics();renderPriority();renderRanking();renderJournals();renderSources();}catch(err){el('ranking-list').append(make('div','empty','집계 자료를 불러올 수 없습니다.'));el('priority-grid').append(make('div','empty','데이터를 불러올 수 없습니다. 로컬 파일을 직접 열었다면 웹서버로 실행해 주세요.'));console.error('자료 로딩 오류',err);}}
el('expand-rankings').addEventListener('click',()=>{state.showAllRankings=!state.showAllRankings;renderRanking();});el('query').addEventListener('input',e=>{state.query=e.target.value;renderJournals();});el('sort').addEventListener('change',e=>{state.sort=e.target.value;renderJournals();});el('only-priority').addEventListener('change',e=>{state.onlyPriority=e.target.checked;renderJournals();});boot();
