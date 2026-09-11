// Внешние тексты вставляем только через textContent, никогда через innerHTML.
const $ = id => document.getElementById(id);
let data = { jobs: [], sources: [] };
const DAY = 72*60*60*1000;
const el = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
function link(text, url, cls) { const a = el('a',text,cls); try { const u = new URL(url); if(u.protocol !== 'https:') return el('span',text); a.href=u.href; } catch { return el('span',text); } a.target='_blank'; a.rel='noopener noreferrer'; return a; }
function ageLabel(date) {
 const minutes=Math.max(0,Math.floor((Date.now()-Date.parse(date))/60000));
 if(minutes>=1440)return new Intl.RelativeTimeFormat('ru',{numeric:'always'}).format(-Math.floor(minutes/1440),'day');
 if(minutes<1)return 'Только что';
 return new Intl.RelativeTimeFormat('ru',{numeric:'always'}).format(-Math.floor(minutes<60?minutes:minutes/60),minutes<60?'minute':'hour');
}
function render() {
 const opened=new Set([...document.querySelectorAll('.card details[open]')].map(x=>x.closest('.card').dataset.id));
 const format=$('format').value, now=Date.now();
 const jobs=data.jobs.filter(j=>{
  const age=now-Date.parse(j.date);
  return !j.closed && Number.isFinite(age) && age>=0 && age<DAY && (!format || j.formats.includes(format) || format==='Игровые видео' && /minecraft|майнкрафт|roblox|cs2|киберспорт|игров/i.test(j.text));
 });
 jobs.sort((a,b)=>Date.parse(b.date)-Date.parse(a.date));
 $('count').textContent=`Вакансии · ${jobs.length}`; $('jobs').replaceChildren();
 if(!jobs.length) $('jobs').append(el('p','Свежих вакансий'+($('format').value?' в категории «'+$('format').value+'»':'')+' за последние три дня нет. Время последнего успешного сбора указано сверху.','empty'));
 for(const j of jobs){const card=el('article',undefined,'card'),body=el('div'),aside=el('div',undefined,'aside');
 card.dataset.id=j.id;
 const stamp=el('div',ageLabel(j.date)+(j.digest?' · дата подборки':'')+' · '+j.sources.map(s=>s.name).join(' / '),'meta');stamp.title=new Date(j.date).toLocaleString('ru-RU');body.append(stamp,el('h3',j.title));
 const tags=el('div',undefined,'tags'); [...j.formats,...(j.flags||[])].forEach(f=>tags.append(el('span',f,'tag')));body.append(tags);
 const brief=j.brief||{};const facts=el('dl',undefined,'facts');
 for(const [label,value] of [['Задача',brief.task],['Объём',brief.volume],['Бюджет',j.pay.length?j.pay.join(' · '):null],['Срок',brief.deadline]]){facts.append(el('dt',label),el('dd',value||'Не указано'));}body.append(facts);
 const details=el('details');details.open=opened.has(j.id);details.append(el('summary','Полный текст объявления'),el('p',j.text,'full'));body.append(details);
 aside.append(el('div',j.pay.length?j.pay.join(' · '):'Оплата не указана','money'));
 if(j.pay.length) aside.append(el('div','Суммы из текста, не нормализованная ставка','unknown'));
 if(j.risks.length) j.risks.forEach(r=>aside.append(el('div',r,'risk')));else aside.append(el('p','Явных признаков по правилам не найдено. Автор не проверен.','unknown'));
 const contacts=el('div',undefined,'contacts');contacts.append(el('div','Контакты из объявления','unknown'));for(const c of j.contacts){contacts.append(el('div',c));}if(!j.contacts.length)contacts.append(el('div','Смотрите оригинал: там может быть анкета.'));aside.append(contacts);
 const replies=j.replyContacts||[];
 for(const c of replies){
  if(/^@[A-Za-z][A-Za-z0-9_]{3,31}$/.test(c))aside.append(link('Написать '+c+' ↗','https://t.me/'+c.slice(1),'primary'));
  else if(/^[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$/.test(c)){const mail=el('a','Написать на почту ↗','primary');mail.href='mailto:'+c;aside.append(mail);}
 }
 if(!replies.length)aside.append(el('p','Контакт для отклика не определён — смотрите оригинал.','unknown'));
 const originals=el('div',undefined,'originals');j.sources.forEach(src=>originals.append(link('Оригинал: '+src.name+' ↗',src.url)));aside.append(originals);
 card.append(body,aside);$('jobs').append(card);
 }
}
async function load(){ if($('refresh').disabled)return; $('refresh').disabled=true;$('refresh').textContent='Проверяю список…'; try {const response=await fetch('data/jobs.json?t='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error();const result=await response.json();if(!Array.isArray(result.jobs)||!Array.isArray(result.sources))throw Error();data=result;
 const date=data.lastSuccessAt?new Date(data.lastSuccessAt):null;
 $('updated').textContent=date?'Последний успешный сбор: '+date.toLocaleString('ru-RU'):'Успешного сбора ещё не было';
 $('message').textContent=!date?'Нет подтверждённого обновления. Проверьте источники.':Date.now()-date.getTime()>3*3600000?'Данные не обновлялись больше трёх часов. Проверьте запуск сборщика.':data.sources.some(s=>!s.ok)?'Часть источников недоступна. Сохранены ранее найденные объявления.':'';
 $('sources').replaceChildren();for(const s of [...data.sources].sort((a,b)=>(b.jobs7d||0)-(a.jobs7d||0))){const row=el('div',undefined,'source');row.append(link(s.name,s.url),el('div',(s.ok?'✓ ':'! ')+s.message+(s.ok?` · новых: ${s.newCount||0} · вакансий за сутки: ${s.jobs24h||0} · проверено постов: ${s.postsScanned||0}`:'')));row.append(el('p',`Найдено за 7 дней: ${s.jobs7d||0} уникальных заказов · ${s.exclusive7d||0} найдены только в этом канале · ${s.shared7d||0} также в других источниках`,'source-value'));if(s.jobs7d===0)row.append(el('p','Нет подходящих находок за неделю — кандидат на замену после проверки полноты сбора.','unknown'));if(s.latestJobAt)row.append(el('div','Последняя вакансия: '+new Date(s.latestJobAt).toLocaleString('ru-RU'),'unknown')); if(s.note)row.append(el('p',s.note,'unknown')); $('sources').append(row);}render();
 }catch{$('message').textContent='Не удалось загрузить список. Откройте сайт через веб-сервер или GitHub Pages и проверьте соединение.';}finally{$('refresh').disabled=false;$('refresh').textContent='Обновить список';}}
 $('format').addEventListener('input',render);
 $('refresh').addEventListener('click',load);load();
 // Кнопка и таймер перечитывают готовый список; сбор запускает GitHub Actions.
 setInterval(load, 5*60*1000);

// Убираем просроченные карточки даже если вкладка открыта и сборщик недоступен.
setInterval(render, 30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden){render();load();}});
