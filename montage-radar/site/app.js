// Внешние тексты вставляем только через textContent, никогда через innerHTML.
const $ = id => document.getElementById(id);
let data = { jobs: [], sources: [] };
const DAY = 24*60*60*1000;
const el = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
function link(text, url, cls) { const a = el('a',text,cls); try { const u = new URL(url); if(u.protocol !== 'https:') return el('span',text); a.href=u.href; } catch { return el('span',text); } a.target='_blank'; a.rel='noopener noreferrer'; return a; }
function render() {
 const format=$('format').value, now=Date.now();
 const jobs=data.jobs.filter(j=>{
  const age=now-Date.parse(j.date);
  return !j.closed && Number.isFinite(age) && age>=0 && age<DAY && (!format || j.formats.includes(format) || format==='Игровые видео' && /minecraft|майнкрафт|roblox|cs2|киберспорт|игров/i.test(j.text));
 });
 jobs.sort((a,b)=>Date.parse(b.date)-Date.parse(a.date));
 $('count').textContent=`Вакансии · ${jobs.length}`; $('jobs').replaceChildren();
 if(!jobs.length) $('jobs').append(el('p','За последние сутки в этой категории вакансий нет. Новые появятся после очередного сбора.','empty'));
 for(const j of jobs){const card=el('article',undefined,'card'),body=el('div'),aside=el('div',undefined,'aside');
 body.append(el('div',new Date(j.date).toLocaleString('ru-RU',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+' · '+j.sources.map(s=>s.name).join(' / '),'meta'),el('h3',j.title));
 const tags=el('div',undefined,'tags'); [...j.formats,...(j.flags||[])].forEach(f=>tags.append(el('span',f,'tag')));body.append(tags);
 body.append(el('p',j.text.slice(0,310)+(j.text.length>310?'…':''),'excerpt'));
 const details=el('details');details.append(el('summary','Полный текст объявления'),el('p',j.text,'full'));body.append(details);
 aside.append(el('div',j.pay.length?j.pay.join(' · '):'Оплата не указана','money'));
 if(j.pay.length) aside.append(el('div','Суммы из текста, не нормализованная ставка','unknown'));
 if(j.risks.length) j.risks.forEach(r=>aside.append(el('div',r,'risk')));else aside.append(el('p','Явных признаков по правилам не найдено. Автор не проверен.','unknown'));
 const contacts=el('div',undefined,'contacts');contacts.append(el('div','Контакты из объявления','unknown'));for(const c of j.contacts){contacts.append(el('div',c));}if(!j.contacts.length)contacts.append(el('div','Смотрите оригинал: там может быть анкета.'));aside.append(contacts);
 aside.append(link('Открыть оригинал ↗',j.sources[0].url,'primary'));
 card.append(body,aside);$('jobs').append(card);
 }
}
async function load(){ $('refresh').disabled=true; try {const response=await fetch('data/jobs.json?t='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error();const result=await response.json();if(!Array.isArray(result.jobs)||!Array.isArray(result.sources))throw Error();data=result;
 const date=data.lastSuccessAt?new Date(data.lastSuccessAt):null;
 $('updated').textContent=date?'Последний успешный сбор: '+date.toLocaleString('ru-RU'):'Успешного сбора ещё не было';
 $('message').textContent=!date?'Нет подтверждённого обновления. Проверьте источники.':Date.now()-date.getTime()>3*3600000?'Данные не обновлялись больше трёх часов. Проверьте запуск сборщика.':data.sources.some(s=>!s.ok)?'Часть источников недоступна. Сохранены ранее найденные объявления.':'';
 $('sources').replaceChildren();for(const s of data.sources){const row=el('div',undefined,'source');row.append(link(s.name,s.url),el('div',(s.ok?'✓ ':'! ')+s.message+(s.ok?` · новых: ${s.newCount||0} · вакансий за сутки: ${s.jobs24h||0} · проверено постов: ${s.postsScanned||0}`:'')));if(s.latestJobAt)row.append(el('div','Последняя вакансия: '+new Date(s.latestJobAt).toLocaleString('ru-RU'),'unknown')); if(s.note)row.append(el('p',s.note,'unknown')); $('sources').append(row);}render();
 }catch{$('message').textContent='Не удалось загрузить список. Откройте сайт через веб-сервер или GitHub Pages и проверьте соединение.';}finally{$('refresh').disabled=false;}}
 $('format').addEventListener('input',render);
 $('refresh').addEventListener('click',load);load();
 // Кнопка и таймер перечитывают готовый список; сбор запускает GitHub Actions.
 setInterval(load, 5*60*1000);

// Убираем просроченные карточки даже если вкладка открыта и сборщик недоступен.
setInterval(render, 30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden){render();load();}});
