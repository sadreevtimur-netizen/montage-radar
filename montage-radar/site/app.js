// Внешние тексты вставляем только через textContent, никогда через innerHTML.
const $ = id => document.getElementById(id);
let data = { jobs: [], sources: [] }, states = {};
let previousVisit = Date.now() - 86400000;
try { const stored=Number(localStorage.getItem('hiki-radar-last-visit')); if(stored>0) previousVisit=stored; } catch {}
const isFresh = j => Date.parse(j.firstSeenAt || j.date) > previousVisit;
try { states = JSON.parse(localStorage.getItem('hiki-radar-v1') || '{}'); } catch {}
const el = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
function link(text, url, cls) { const a = el('a',text,cls); try { const u = new URL(url); if(u.protocol !== 'https:') return el('span',text); a.href=u.href; } catch { return el('span',text); } a.target='_blank'; a.rel='noopener noreferrer'; return a; }
function setState(id, state) { states[id] = states[id] === state ? '' : state; try {localStorage.setItem('hiki-radar-v1',JSON.stringify(states));} catch {$('message').textContent='Браузер не разрешил сохранить отметки.';} render(); }
function render() {
 const query=$('q').value.toLowerCase().trim(), format=$('format').value, status=$('status').value;
 const jobs=data.jobs.filter(j=>{
  const st=states[j.id]||'', flags=j.flags||[];
  const matchesState = status==='all'||status==='new'&&!st||status==='fresh'&&isFresh(j)&&!st||status==='closed'&&j.closed||st===status;
  return (!j.closed||['closed','all','saved','sent'].includes(status)) && matchesState &&
   (!query||(j.title+' '+j.text).toLowerCase().includes(query))&&(!format||j.formats.includes(format))&&
   (!$('pay').checked||j.pay.length)&&((Date.now()-Date.parse(j.date))/86400000<=Number($('age').value))&&
   (!$('source').value||j.sources.some(s=>new URL(s.url).pathname.split('/')[1].toLowerCase()===$('source').value))&&
   (!$('no-shoot').checked||!flags.some(f=>['Нужна съёмка','Офис'].includes(f)));
 });
 const fit = j => (/minecraft|майнкрафт|roblox|cs2|киберспорт|игров/i.test(j.text)?2:0)+(/youtube|ютуб|ютьюб|подкаст/i.test(j.text)?1:0);
 jobs.sort((a,b)=>($('sort').value==='fit'?fit(b)-fit(a):0)||Date.parse(b.date)-Date.parse(a.date));
 $('count').textContent=`Вакансии · ${jobs.length}`; $('jobs').replaceChildren();
 if(!jobs.length) $('jobs').append(el('p','По этим условиям объявлений нет. Попробуйте изменить фильтры или проверить состояние источников.','empty'));
 for(const j of jobs){const card=el('article',undefined,'card'),body=el('div'),aside=el('div',undefined,'aside');
 body.append(el('div',new Date(j.date).toLocaleDateString('ru-RU')+' · '+j.sources.map(s=>s.name).join(' / '),'meta'),el('h3',j.title));
 const tags=el('div',undefined,'tags'); [...j.formats,...(j.flags||[]),...(j.closed?['Поиск закрыт']:isFresh(j)?['С прошлого визита']:[])].forEach(f=>tags.append(el('span',f,'tag')));body.append(tags);
 body.append(el('p',j.text.slice(0,310)+(j.text.length>310?'…':''),'excerpt'));
 const details=el('details');details.append(el('summary','Полный текст объявления'),el('p',j.text,'full'));body.append(details);
 aside.append(el('div',j.pay.length?j.pay.join(' · '):'Оплата не указана','money'));
 if(j.pay.length) aside.append(el('div','Суммы из текста, не нормализованная ставка','unknown'));
 if(j.risks.length) j.risks.forEach(r=>aside.append(el('div',r,'risk')));else aside.append(el('p','Явных признаков по правилам не найдено. Автор не проверен.','unknown'));
 const contacts=el('div',undefined,'contacts');contacts.append(el('div','Контакты из объявления','unknown'));for(const c of j.contacts){contacts.append(el('div',c));}if(!j.contacts.length)contacts.append(el('div','Смотрите оригинал: там может быть анкета.'));aside.append(contacts);
 aside.append(link('Открыть оригинал ↗',j.sources[0].url,'primary'));
 const actions=el('div',undefined,'actions');for(const [s,label] of [['seen','Просмотрел'],['saved','Сохранить'],['sent','Написал'],['hidden','Скрыть']]){const b=el('button',(states[j.id]===s?'✓ ':'')+label);b.setAttribute('aria-pressed',String(states[j.id]===s));b.addEventListener('click',()=>setState(j.id,s));actions.append(b);}aside.append(actions);card.append(body,aside);$('jobs').append(card);
 }
}
async function load(){ $('refresh').disabled=true; try {const response=await fetch('data/jobs.json?t='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error();const result=await response.json();if(!Array.isArray(result.jobs)||!Array.isArray(result.sources))throw Error();data=result;
 try {localStorage.setItem('hiki-radar-last-visit',String(Date.now()));} catch {}
 const chosen=$('source').value; $('source').replaceChildren(el('option','Все источники')); $('source').firstChild.value=''; for(const src of data.sources){const o=el('option',src.name);o.value=(src.id||new URL(src.url).pathname.slice(1)).toLowerCase();$('source').append(o);} $('source').value=chosen;
 $('fresh-summary').textContent=`За последний сбор: ${data.newCount||0} новых уникальных объявлений. С прошлого визита: ${data.jobs.filter(j=>!j.closed&&isFresh(j)).length} (до фильтров).`; 
 const date=data.lastSuccessAt?new Date(data.lastSuccessAt):null;
 $('updated').textContent=date?'Последний успешный сбор: '+date.toLocaleString('ru-RU'):'Успешного сбора ещё не было';
 $('message').textContent=!date?'Нет подтверждённого обновления. Проверьте источники.':Date.now()-date.getTime()>3*3600000?'Данные не обновлялись больше трёх часов. Проверьте запуск сборщика.':data.sources.some(s=>!s.ok)?'Часть источников недоступна. Сохранены ранее найденные объявления.':'';
 $('sources').replaceChildren();for(const s of data.sources){const row=el('div',undefined,'source');row.append(link(s.name,s.url),el('div',(s.ok?'✓ ':'! ')+s.message+(s.ok?` · новых: ${s.newCount||0} · вакансий за 7 дней в базе: ${s.jobs7d||0} · проверено постов: ${s.postsScanned||0}`:'')));if(s.latestJobAt)row.append(el('div','Последняя вакансия: '+new Date(s.latestJobAt).toLocaleString('ru-RU'),'unknown')); if(s.note)row.append(el('p',s.note,'unknown')); $('sources').append(row);}render();
 }catch{$('message').textContent='Не удалось загрузить список. Откройте сайт через веб-сервер или GitHub Pages и проверьте соединение.';}finally{$('refresh').disabled=false;}}
 for(const id of ['q','format','status','age','pay','source','sort','no-shoot']) $(id).addEventListener('input',render);
 $('refresh').addEventListener('click',load);load();
 // Кнопка и таймер перечитывают готовый список; сбор запускает GitHub Actions.
 setInterval(load, 5*60*1000);
