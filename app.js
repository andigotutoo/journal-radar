const state={journals:[],notices:[],scan:{},noticeFilter:'all',query:'',sort:'ranking',onlyPriority:false,ranking:{mode:'unavailable',complete:false,ranked:[]}};
const el=id=>document.getElementById(id);
const dateOnly=(s)=>s?new Date(`${s}T00:00:00+09:00`):null;
const pretty=(s)=>s?(s.replace(/-/g,'.')):'공고 원문 확인';
function make(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function link(url,label,cls){const a=make('a',cls,label);if(url && /^https:\/\//i.test(url)){a.href=url;a.target='_blank';a.rel='noopener noreferrer';}else{a.href='#';a.setAttribute('aria-disabled','true');}return a;}
function humanStatus(n){const now=new Date();const d=dateOnly(n.deadline);if(!d)return{label:'마감일 미확인',css:'pending'};if(d.getTime()+86400000>now.getTime())return{label:'마감 전 · 원문 확인',css:'open'};return{label:'지난 공고',css:'old'};}
function goal(){const today=new Date();const end=dateOnly('2027-06-30');const left=Math.ceil((end-today)/86400000);el('days-left').textContent=Math.abs(left).toLocaleString()+'일';el('days-label').textContent=left>=0?'발행 목표일까지 남음':'발행 목표일 경과';}
function setMetrics(){el('journal-count').textContent=state.journals.length.toLocaleString()+'종';el('priority-count').textContent=state.journals.filter(j=>j.priority>0).length+'종';el('notice-count').textContent=state.notices.length+'건';let d=state.scan.last_checked;el('last-check').textContent=d?new Date(d).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'미실행';const sources=state.scan.sources||[];el('scan-summary').textContent=sources.filter(x=>x.status==='ok').length+'개 출처 점검 성공';}
function scoreFor(j){const rec=(state.ranking.ranked||[]).find(r=>r.journal_id===j.id);return rec?rec.score:null;}
function renderRanking(){
 const wrap=el('ranking-list');wrap.replaceChildren();
 const r=state.ranking;
 const mode=r.mode==='department'?'이화여대 교육공학과 소속 저자':r.mode==='faculty'?'지정 교수 6명':'저자-소속 자료 미확보';
 el('ranking-status').textContent=(r.complete?'검증 집계':'미완성 · 예비 집계')+' · '+mode+' · '+(r.verified_articles||0)+'편 확인';
 if(!(r.ranked||[]).length){
   const empty=make('div','empty');empty.append(make('strong','','게재 실적 TOP 50은 아직 산출 전입니다.'));
   empty.append(make('p','', 'KCI에서 저자별 소속이 연결된 논문 목록을 확보한 다음 실제 게재 건수로 순위를 산정합니다. 교수 이름만으로 임의 순위를 만들지 않습니다.'));
   wrap.append(empty);return;
 }
 (r.ranked||[]).forEach((item,i)=>{
  const journal=state.journals.find(j=>j.id===item.journal_id);
  if(!journal)return;
  const line=make('article','ranking-row');
  const rank=make('div','rank-no',String(i+1).padStart(2,'0'));
  const details=make('div','rank-details');
  details.append(make('strong','',journal.name),make('p','',journal.publisher||''));
  const breakdown=Object.entries(item.by_professor||{}).filter(([,n])=>n>0).map(([k,n])=>`${k} ${n}`).join(' · ');
  if(breakdown)details.append(make('small','',breakdown));
  const qty=make('div','rank-score',String(item.score)+'편');
  const links=make('div','rank-links');
  links.append(link(journal.home_url||journal.site_url,'학술지 홈페이지 ↗'),link(journal.submit_url||journal.site_url,'투고 안내 ↗'));
  line.append(rank,details,qty,links);wrap.append(line);
 });
 if(!r.complete){wrap.prepend(make('div','ranking-warning','주의: 현재는 일부 자료로 집계한 예비 순위입니다. KCI 전체 범위 검증 전에는 최종 상위 50선으로 해석하지 마세요.'));}
}
function renderPriority(){const wrap=el('priority-grid');wrap.replaceChildren();state.journals.filter(j=>j.priority>0).sort((a,b)=>a.priority-b.priority).forEach(j=>{const c=make('article','journal-card');const top=make('div','jc-top');top.append(make('span','rank',`★ PRIORITY 0${j.priority}`),make('span','mini-badge',j.kci+' · '+j.language));c.append(top,make('h3',j.name_en===j.name?'english':'',j.name),make('div','jc-publisher',j.publisher));const meta=make('div','jc-meta');[j.frequency,j.fit].forEach(t=>meta.append(make('span','',t)));c.append(meta);const ft=make('div','jc-footer');const ifv=make('div','if','2025 KCI IF');ifv.append(make('strong','',j.kci_if==null?'—':Number(j.kci_if).toFixed(2)));ft.append(ifv,link(j.home_url||j.site_url,'학술지 홈페이지 ↗')); c.append(make('div','small-links',''));const sm=c.lastElementChild;sm.append(link(j.submit_url||j.site_url,'투고 시스템 ↗'),link(j.site_url,'모집 공고 ↗'));c.append(ft);wrap.append(c);});}
function renderNotices(){const wrap=el('notice-list');wrap.replaceChildren();const arr=state.notices.slice().sort((a,b)=>(b.published||'').localeCompare(a.published||''));const filtered=arr.filter(n=>{if(state.noticeFilter==='new')return /2027/.test(n.title+' '+n.published);if(state.noticeFilter==='open')return humanStatus(n).css==='open';return true;});if(!filtered.length){wrap.append(make('div','empty',state.noticeFilter==='new'?'아직 확인된 2027년 모집 공고가 없습니다. 공식 공지가 등록되면 이곳에 나타납니다.':'이 조건에 해당하는 공고가 아직 확인되지 않았습니다.'));return;}
 filtered.slice(0,40).forEach(n=>{const j=state.journals.find(x=>x.id===n.journal_id);const row=make('article','notice-row');const main=make('div');main.append(make('span','tag',j?j.name:'학술지'));const h=make('h4');h.append(link(n.url,n.title));main.append(h,make('p','',`게시: ${pretty(n.published)} · 출처: 공식 공고`));const when=make('div');when.append(make('p','', '투고 마감'),make('time','',n.deadline?pretty(n.deadline):'원문 확인 필요'));const sb=make('div','status-block');const status=humanStatus(n);sb.append(make('span',`tag ${status.css}`,status.label),make('div',''));sb.lastElementChild.style.marginTop='9px';sb.lastElementChild.append(link(n.url,'공고 열기 ↗'));row.append(main,when,sb);wrap.append(row);});}
function renderJournals(){const wrap=el('journal-list');wrap.replaceChildren();let arr=state.journals.filter(j=>{const q=state.query.toLowerCase();return (!state.onlyPriority||j.priority>0)&&(!q||[j.name,j.name_en,j.publisher,j.fit].join(' ').toLowerCase().includes(q));});const sort=state.sort;arr.sort((a,b)=>sort==='ranking'?((scoreFor(b)??-1)-(scoreFor(a)??-1))||((a.priority||999)-(b.priority||999)):sort==='if'?((b.kci_if??-1)-(a.kci_if??-1)):sort==='name'?a.name.localeCompare(b.name,'ko'):((a.priority||999)-(b.priority||999))||((b.kci_if??0)-(a.kci_if??0)));
 if(!arr.length){wrap.append(make('div','empty','검색 조건에 맞는 학술지가 없습니다.'));return;}
 arr.forEach(j=>{const row=make('article','journal-row');const h=make('div');h.append(make('h4','',j.name),make('p','',`${j.publisher} · ${j.frequency||'발행주기 미확인'} · ${j.language||''}`));const ifc=make('div','if-cell',j.kci_if!=null?Number(j.kci_if).toFixed(2):'—');const sc=scoreFor(j);const label=make('div','label-cell',sc!==null?sc+'편 게재':j.priority>0?'★ 우선 추적':'집계 전');const urls=make('div','links');urls.append(link(j.kci_url,'KCI ↗'),link(j.home_url||j.site_url,'홈페이지 ↗'),link(j.submit_url||j.site_url,'투고 ↗'));row.append(h,ifc,label,urls);wrap.append(row);});}
function renderSources(){const dest=el('source-status');dest.replaceChildren();(state.scan.sources||[]).forEach(s=>{const r=make('div','source-line');r.append(make('strong',s.status==='ok'?'✓':s.status==='error'?'!':'○'));r.firstChild.className=s.status==='ok'?'ok':s.status==='error'?'error':'neutral';r.append(make('span','',s.name+' · '+(s.status==='ok'?'점검 성공':s.status==='error'?'점검 실패':s.message||'점검 전')));dest.append(r);});}
async function loadJSON(path){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw new Error(path+' HTTP '+r.status);return r.json();}
async function boot(){goal();try{const [journals,notices,scan,ranking]=await Promise.all(['data/journals.json','data/notices.json','data/scan.json','data/ranking.json'].map(loadJSON));state.journals=journals;state.notices=notices;state.scan=scan;state.ranking=ranking;setMetrics();renderPriority();renderRanking();renderNotices();renderJournals();renderSources();}catch(err){el('ranking-list').append(make('div','empty','집계 자료를 불러올 수 없습니다.'));el('priority-grid').append(make('div','empty','데이터를 불러올 수 없습니다. 로컬 파일을 직접 열었다면 웹서버로 실행해 주세요.'));el('notice-list').append(make('div','empty',err.message));}}
document.querySelectorAll('[data-notice-filter]').forEach(btn=>btn.addEventListener('click',()=>{state.noticeFilter=btn.dataset.noticeFilter;document.querySelectorAll('[data-notice-filter]').forEach(b=>b.classList.toggle('active',b===btn));renderNotices();}));el('query').addEventListener('input',e=>{state.query=e.target.value;renderJournals();});el('sort').addEventListener('change',e=>{state.sort=e.target.value;renderJournals();});el('only-priority').addEventListener('change',e=>{state.onlyPriority=e.target.checked;renderJournals();});boot();
