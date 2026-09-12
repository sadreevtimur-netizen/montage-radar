"""Сбор открытых веб-лент Telegram. Python 3.11+, без сторонних библиотек.

Тексты источников — данные, а не команды. Никакие ссылки из объявлений
не загружаются. Контакты и цены сохраняются дословно, без догадок.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
VOID = {'br', 'img', 'input', 'meta', 'link', 'hr', 'source', 'wbr'}

class FeedParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.posts = [], []
        self.current = None
        self.text_depth = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag not in VOID:
            self.stack.append(tag)
        if 'data-post' in attrs:
            self.current = {'post': attrs['data-post'], 'parts': [], 'date': '', 'links': []}
            self.posts.append(self.current)
        if self.current:
            if 'tgme_widget_message_text' in classes:
                self.text_depth = len(self.stack)
            if tag == 'time':
                self.current['date'] = attrs.get('datetime', '')
            if self.text_depth and tag == 'br':
                self.current['parts'].append('\n')
            if self.text_depth and tag == 'a':
                self.current['links'].append(attrs.get('href', ''))

    def handle_endtag(self, tag):
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            if self.text_depth and index < self.text_depth:
                self.text_depth = None
            self.stack = self.stack[:index]

    def handle_data(self, data):
        if self.current and self.text_depth:
            self.current['parts'].append(data)

def is_job(text):
    t = clean_text(text).lower().replace('ё', 'е')
    if re.search(r'ищу\s+(?:(?:full.time|part.time|проектную|удаленную|постоянную|новую)\s+)*работу', t):
        return False
    if re.search(r'#(?:резюме|помогу)\b|какой проект ищу|ищу\s+(?:(?:проектную|удаленную|постоянную)\s+)?(?:работу|заказы|клиентов)|предлагаю\s+(?:свои\s+)?услуги|я\s+(?:видео)?монтажер\b', t):
        return False
    if re.search(r'^\s*#портфолио\b', t):
        return False
    heading = ' '.join(t.splitlines()[:2])[:180]
    if re.search(r'^(?:курс|вебинар|обучение монтажу)\b|научим монтировать|запишись на курс|набор на (?:курс|обучение)|на обучение', heading) and not re.search(r'ищем преподавателя', heading):
        return False
    if re.search(r'(?:ищем|ищу|нужен|требуется|вакансия)\s*[:—-]?\s*(?:smm|смм|видеооператор|оператор|сценарист|контент.менеджер)', heading):
        return False
    role = r'(?:видео)?монтаж[её]р\w*|режиссер\w*\s+монтажа|видеоредактор\w*|video\s*editor|моуш[ен]*[ -]?дизайнер\w*|motion[ -]?designer|рилс[ -]?мейкер\w*|reels[ -]?мейкер\w*'
    if re.search(rf'\bя\s+(?:(?:2d|3d|2d/3d|опытный|начинающий)\s+)?(?:{role})', t[:350]):
        return False
    if re.search(r'video editor|video editing', t[:220]) and re.search(r'pay|paid|per video|apply|your reply|hiring|looking for', t) and not re.search(r'i am|i’m|i offer|looking for work|my services', t):
        return True
    demand = r'ищу|ищем|ищут|нужен|нужны|требуется|требуются|требуем|вакансия'
    # «Монтажные вставки» в вакансии сценариста больше не делают её вакансией монтажёра.
    if re.search(rf'(?:{demand})[^\n.!?]{{0,75}}(?:{role})', t):
        return True
    title = ' '.join(l for l in t.splitlines() if l.strip() and not l.strip().startswith('#'))[:220]
    if re.search(role, title) and re.search(r'обязанност|задачи|требован|условия|отклик|ищ[уе]|нуж|ваканси', t):
        return True
    return bool(re.search(r'(?:ищу|ищем|ищут|нужен|требуется)[^\n.!?]{0,65}(?:специалист|человек|исполнител)[^\n.!?]{0,45}монтаж|нуж(?:но|ен)\s+(?:сделать\s+)?(?:видео)?монтаж', t))

def clean_text(text):
    # Удаляем только узнаваемые рекламные хвосты каналов, оставляя исходник по ссылке.
    return re.split(r'Как выявить мошенника|Больше вакансий тут|Как не нарваться на мошенническую|📌Разместить вакансию|✅50 вакансий', text, flags=re.I)[0].strip()

def is_closed(text):
    return bool(re.search(r'поиск\s+(?:остановлен|закрыт|заверш[её]н)|вакансия\s+(?:закрыта|неактуальна)|(?:монтаж[её]р|исполнитель|кандидат)\s+найден|набор\s+закрыт', text, re.I))

def work_flags(text):
    t = text.lower().replace('ё', 'е')
    flags = []
    positive_lines = '\n'.join(l for l in t.splitlines() if not re.search(r'не\s+нуж[ен]|не\s+требуется|без\s+съем|не\s+нужно\s+снимать', l))
    if re.search(r'выезжать|выезд\w*\s+на|съемка\s+видео|снимать\s+(?:и|на|по|ролик|видео|reels|shorts|backstage)|съемк[аи]\s*\+\s*монтаж|снимать.{0,30}монтировать|свой\s+комплект\s+оборудования|видеооператор', positive_lines):
        flags.append('Нужна съёмка')
    if re.search(r'работа\s+в\s+офисе|формат\s*[:—-]?\s*офис|полностью\s+офис|только\s+офис|преимущественно\s+офлайн', t):
        flags.append('Офис')
    if re.search(r'сценарист|smm|смм|контент.план|выкладывать|публиковать|публикация', t):
        flags.append('Дополнительные обязанности')
    return flags

def inspect_risks(text):
    """Прозрачные эвристики. Отсутствие срабатываний не означает безопасность."""
    risks = []
    sentences = re.split(r'[.!?\n]+', text.lower())
    for s in sentences:
        # Не обвиняем автора за предупреждения «никогда не присылайте код».
        if re.search(r'не\s+(?:нужно|нужна|требуется|платите|оплачивайте|отправляйте|присылайте|сообщайте)|никогда|без\s+(?:взнос|оплат|предоплат)', s):
            continue
        if re.search(r'страхов\w*\s+взнос|оплат\w*\s+(?:доступ|регистрац|обучен)|внес\w*\s+(?:залог|депозит)', s):
            risks.append('Упоминается платёж со стороны исполнителя — уточните, за что и кому.')
        if re.search(r'(?:пришл|отправ|сообщ)\w*.{0,30}код.{0,25}(?:вход|telegram|телеграм|смс|sms)', s):
            risks.append('Просят код входа или из SMS — не передавайте его.')
        if re.search(r'(?:установ|скача)\w*.{0,70}(?:\.exe|anydesk|teamviewer|программ)', s):
            risks.append('Просят установить программу — проверьте официальный источник и назначение.')
    if re.search(r'тестов', text, re.I):
        risks.append('Есть тестовое: уточните объём, оплату и использование результата.')
    return list(dict.fromkeys(risks))

def normalize(text):
    t = re.sub(r'https?://\S+|@\w+|#\w+', ' ', text.lower())
    t = re.sub(r'[^\w\s]', ' ', t)
    return ' '.join(t.split())

def contacts(text, links):
    values = re.findall(r'(?<![\w.])@[a-zA-Z][a-zA-Z0-9_]{3,31}\b|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}', text)
    for url in links:
        if re.match(r'^https://t\.me/[A-Za-z][A-Za-z0-9_]{3,31}$', url):
            values.append('@' + url.rsplit('/', 1)[-1])
    return list(dict.fromkeys(values))

def brief(text):
    """Только дословные фрагменты. Не додумываем объём, цену и сроки."""
    lines = [re.sub(r'#\w+', '', x).strip(' \u200b•—-') for x in re.split(r'[\n;]+', text)]
    lines = [x for x in lines if x]
    def pick(pattern):
        return next((x[:280] for x in lines if re.search(pattern, x, re.I)), None)
    return {
        'task': pick(r'^(?:задач[аи]|обязанности)\s*[:—-].+|монтировать|собирать\s+(?:ролик|видео)|монтаж\s+(?:ролик|видео|reels|shorts|подкаст)|создавать\s+(?:анимац|видео)') or pick(r'монтир|монтаж|reels|shorts|подкаст|анимац|motion'),
        'volume': pick(r'\d+\s*(?:[-–]\s*\d+\s*)?(?:(?:коротких|длинных)\s+)?(?:ролик|видео|reels|shorts|выпуск)|объ[её]м\s*:'),
        'deadline': pick(r'дедлайн|срок(?:и|а)?\s*[:—-]|до\s+\d{1,2}[./]|за\s+\d+\s*(?:дн|день|час)|сдать\s+до'),
    }

def reply_contacts(text, links=(), excluded=()):
    """Контакт для отклика — только рядом с явным приглашением написать."""
    found = []
    excluded = {x.lower().lstrip('@') for x in excluded}
    lines = text.splitlines()
    prompt = r'отклик|писать|пишите|связ[ьи]|контакт|отправ|присыл|пришл'
    noise = r'реклам|разместить|подпис|наш канал'
    for index, line in enumerate(lines):
        if re.search(noise, line, re.I) or not re.search(prompt, line, re.I):
            continue
        # Соседнюю строку берём лишь при отсутствии контакта в текущей.
        urls = re.findall(r'https://t\.me/[A-Za-z][A-Za-z0-9_]{3,31}\b', line)
        values = contacts(line, urls)
        if not values and index + 1 < len(lines):
            following = lines[index + 1].strip()
            if not re.search(noise, following, re.I) and re.fullmatch(r'[@\w.+:/ -]+', following):
                values = contacts(following, re.findall(r'https://t\.me/[A-Za-z][A-Za-z0-9_]{3,31}\b', following))
        for c in values:
            if c.lower().lstrip('@') in excluded or c.lower().endswith('bot'):
                continue
            if c not in found:
                found.append(c)
    return found

def extract_pay(text):
    """Разбираем суммы построчно: цифры соседнего пункта не входят в бюджет."""
    number = r'\d+(?:[ \u00a0]\d{3})*(?:[.,]\d+)?'
    currency = r'(?:₽|руб\w*|\$|€|USD|EUR|тыс\.?)(?!\w)'
    pattern = rf'(?:от[ ]+|до[ ]+)?{number}(?:[ ]*[–—-][ ]*{number})?[ ]*{currency}'
    result = []
    for line in text.splitlines():
        for match in re.finditer(pattern, line, re.I):
            amount = match.group().strip()
            tail = line[match.end():]
            unit = re.match(r'[ ,]*(?:/\s*|за\s+|в\s+)(?:один\s+)?(?:ролик|видео|проект|месяц|мес\.?|час|минут\w*|выпуск)\w*', tail, re.I)
            if unit:
                amount += unit.group()
            if amount not in result:
                result.append(amount)
    return result[:4]


def source_metrics(jobs, previous, now):
    """Семь дней уникальных находок; один заказ может иметь несколько источников."""
    cutoff = (now-timedelta(days=7)).isoformat()
    ledger = {x['id']: x for x in previous.get('sourceLedger', []) if x['date'] >= cutoff}
    for j in jobs:
        if j['date'] < cutoff or j.get('closed'):
            continue
        channels = sorted({x['url'].split('/')[3].lower() for x in j['sources']})
        old = ledger.get(j['id'], {})
        ledger[j['id']] = {'id':j['id'], 'date':j['date'], 'channels':sorted(set(channels+old.get('channels', [])))}
    return list(ledger.values())

def make_job(post, source, now):
    text = clean_text(''.join(post['parts']))
    if not is_job(text) or not post['date']:
        return None
    try:
        date = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    if not now - timedelta(days=30) <= date <= now + timedelta(days=1):
        return None
    formats = []
    for name, pattern in [('Короткие видео', r'рилс|reels|shorts|тикток|вертикаль'), ('YouTube', r'youtube|ютуб|ютьюб'), ('Подкасты', r'подкаст|интервью'), ('Анимация', r'анимац|motion|моуш|after effects')]:
        if re.search(pattern, text, re.I):
            formats.append(name)
    amounts = extract_pay(text)
    lines = [re.sub(r'#\w+', '', x).strip(' •—-') for x in text.splitlines() if x.strip()]
    title = next((x for x in lines if len(x) > 15 and not x.startswith('#')), 'Вакансия монтажёра')[:140]
    return {'id': hashlib.sha256(post['post'].encode()).hexdigest()[:16], 'title': title,
            'text': text[:14000], 'date': date.isoformat(), 'checkedAt': now.isoformat(),
            'firstSeenAt': now.isoformat(), 'closed': is_closed(text), 'flags': work_flags(text),
            'brief': brief(text), 'replyContacts': reply_contacts(text, post['links'], [source['id']]),
            'formats': formats or ['Монтаж'], 'pay': amounts[:3], 'contacts': [c for c in contacts(text, post['links']) if c.lower() != '@' + source['id'].lower() and not (c.startswith('@') and c.lower().endswith('bot'))],
            'risks': inspect_risks(text), 'sources': [{'name': source['name'], 'url': 'https://t.me/' + post['post']}]}

def same_digest_job(a, b):
    """Консервативное сопоставление краткой подборки с полным объявлением.
    Нужны общий контакт, формат, числовые условия и совпадение содержания.
    Общий HR-контакт без этих признаков недостаточен.
    """
    if not (a.get('digest') or b.get('digest')):
        return False
    short, full = sorted([a['text'], b['text']], key=len)
    def words(t):
        stop = {'вакансия','монтажер','видеомонтажер','монтаж','нужно','ищем','ищут','работа','контакт','требуется','команда','который','ролики','видео'}
        return {w[:6] for w in normalize(t.replace('ё','е')).split() if len(w)>3 and w not in stop and not w.isdigit()}
    x,y=words(short),words(full)
    numbers=set(re.findall(r'\d+',short))
    formats=[r'подкаст|интервью|talking.head',r'youtube|ютуб',r'reels|рилс|shorts|тикток',r'анимац|motion|моуш']
    shared_format=any(re.search(p,short,re.I) and re.search(p,full,re.I) for p in formats)
    return (shared_format and len(numbers)>=2 and numbers <= set(re.findall(r'\d+',full))
            and len(x)>=8 and len(x&y)/len(x)>=.65)


def deduplicate(jobs):
    groups = {}
    for job in sorted(jobs, key=lambda j: (datetime.fromisoformat(j['date']), j.get('checkedAt', '')), reverse=True):
        key = normalize(job['text'])
        # Дословные и близкие перепосты: общий контакт + совпадение слов >= 90%.
        # Контакт нельзя выкинуть из ключа: одинаковый шаблон у разных заказчиков — разные заявки.
        key = key + ' | ' + ' '.join(sorted(c.lower() for c in job['contacts']))
        match = next((k for k, other in groups.items() if job.get('id') and other.get('id') == job['id']), None)
        if match is None and key in groups:
            match = key
        if match is None and job['contacts']:
            a = set(key.split())
            for k, other in groups.items():
                if {c.lower() for c in job['contacts']} & {c.lower() for c in other['contacts']}:
                    b = set(k.split())
                    if len(a & b) / max(1, len(a | b)) >= .9 or same_digest_job(job, other):
                        match = k
                        break
        if match is None:
            groups[key] = job
        else:
            existing = groups[match]
            if job.get('firstSeenAt', job['date']) < existing.get('firstSeenAt', existing['date']):
                existing['id'] = job['id']
                existing['firstSeenAt'] = job.get('firstSeenAt', job['date'])
            existing['date'] = min(existing['date'], job['date'])
            existing['closed'] = existing.get('closed', False) or job.get('closed', False)
            for src in job['sources']:
                if src not in existing['sources']:
                    existing['sources'].append(src)
    return list(groups.values())

def jobs_from_post(post, source, now):
    """Нумерованные подборки: отдельная карточка и контакт каждого пункта."""
    if source.get('digest'):
        text = ''.join(post['parts'])
        parts = re.split(r'(?m)^\s*\d{1,3}\.[ \t]*(?=#)', text)
        jobs = []
        for section in parts[1:]:
            heading = section.splitlines()[0].lower().replace('ё','е')
            if not re.search(r'монтаж|video.?editor|motion|моуш', heading):
                continue
            # В служебных заголовках нет «ищем», но роль указана явно.
            item = {**post, 'parts':['Вакансия: '+section], 'links':[]}
            job = make_job(item, source, now)
            if job:
                job['id'] = hashlib.sha256((post['post']+'|'+normalize(section)).encode()).hexdigest()[:16]
                job['digest'] = True
                job['replyContacts'] = contacts(section, [])
                jobs.append(job)
        return jobs
    job = make_job(post, source, now)
    return [job] if job else []

def cleanup_due(previous, now):
    if previous.get('retentionHours') != 72:
        return True
    try:
        last = datetime.fromisoformat(previous['lastCleanupAt'].replace('Z','+00:00'))
        return now-last >= timedelta(hours=2)
    except (KeyError, ValueError, TypeError):
        return True


def fetch(url):
    req = Request(url, headers={'User-Agent': 'MontageRadar/1.0 (public vacancy feed reader)'})
    with urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError('HTTP ' + str(response.status))
        return response.read(3_000_000).decode('utf-8')

def merge_observations(previous, fetched, observed_urls, now):
    """Свежий текст заменяет старую версию того же поста, включая закрытие вакансии."""
    by_url = {src['url'].lower(): j for j in previous for src in j['sources']}
    kept = []
    for old in previous:
        sources = [s for s in old['sources'] if s['url'].lower() not in observed_urls]
        if sources:
            kept.append({**old, 'sources': sources})
    for job in fetched:
        old = next((j for j in previous if j['id'] == job['id']), None) if job.get('digest') else next((by_url[s['url'].lower()] for s in job['sources'] if s['url'].lower() in by_url), None)
        if old:
            job['id'] = old['id']
            job['firstSeenAt'] = old.get('firstSeenAt', old['date'])
        kept.append(job)
    return sorted(deduplicate(kept), key=lambda j: j['date'], reverse=True)


def expire_jobs(jobs, previous, now, retention_hours=72, prune=True):
    """В ленте — три дня. От старых постов храним только отпечаток, чтобы не оживлять перепосты."""
    def fingerprint(j):
        value = normalize(clean_text(j['text'])) + '|' + '|'.join(sorted(c.lower() for c in j['contacts']))
        return hashlib.sha256(value.encode()).hexdigest()
    cutoff = (now - timedelta(days=30)).isoformat()
    history = {h['key']: h for h in previous.get('seen', []) if h['date'] >= cutoff}
    for j in previous.get('jobs', []):
        k = fingerprint(j)
        h = {'key': k, 'id': j['id'], 'date': j['date'], 'firstSeenAt': j.get('firstSeenAt', j['date'])}
        if k not in history or h['date'] < history[k]['date']:
            history[k] = h
    active = []
    for j in jobs:
        k = fingerprint(j)
        old = history.get(k)
        if old:
            j['date'] = min(j['date'], old['date'])
            j['id'] = old['id']
            j['firstSeenAt'] = old['firstSeenAt']
        history[k] = {'key': k, 'id': j['id'], 'date': j['date'], 'firstSeenAt': j.get('firstSeenAt', j['date'])}
        published = datetime.fromisoformat(j['date'].replace('Z', '+00:00'))
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if not j.get('closed') and published <= now and (not prune or now - timedelta(hours=retention_hours) < published):
            active.append(j)
    return active, [h for h in history.values() if h['date'] >= cutoff]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT / 'site/data/jobs.json'))
    parser.add_argument('--max-pages', type=int, default=8)
    args = parser.parse_args()
    target = Path(args.output)
    previous = json.loads(target.read_text('utf-8')) if target.exists() else {'jobs': [], 'lastSuccessAt': None}
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=30)).isoformat()
    sources = [s for s in json.loads((ROOT / 'sources.json').read_text('utf-8')) if s.get('enabled')]
    allowed = {s['id'].lower() for s in sources}
    old_jobs = []
    for j in previous['jobs']:
        if j['date'] < cutoff or not is_job(j['text']):
            continue
        j['sources'] = [s for s in j['sources'] if s['url'].split('/')[3].lower() in allowed]
        if j['sources']:
            j.setdefault('firstSeenAt', j['date'])
            j['text'] = clean_text(j['text'])
            j['contacts'] = [c for c in j['contacts'] if not (c.startswith('@') and (c[1:].lower() in allowed or c.lower().endswith('bot')))]
            j['flags'] = work_flags(j['text'])
            j['closed'] = is_closed(j['text'])
            old_jobs.append(j)
    old_ids = {j['id'] for j in old_jobs}
    old_status = {s.get('id', s['url'].rsplit('/', 1)[-1]).lower(): s for s in previous.get('sources', [])}
    fetched, observed, statuses = [], set(), []
    succeeded = 0
    for source in sources:
        ident = source['id']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{3,31}', ident):
            raise ValueError('Invalid source ID')
        seen, count, before, newest, latest_id, pages = set(), 0, '', '', 0, 0
        watermark = old_status.get(ident.lower(), {}).get('latestPostId', 0)
        complete = False
        try:
            for page in range(max(1, min(args.max_pages, 12))):
                feed = FeedParser()
                feed.feed(fetch('https://t.me/s/' + ident + before))
                posts = [p for p in feed.posts if p['date']]
                if not posts:
                    if page == 0:
                        raise RuntimeError('Публичная лента не отдала сообщения')
                    complete = True
                    break
                pages += 1
                ids = []
                for post in posts:
                    pid = int(post['post'].rsplit('/', 1)[-1])
                    ids.append(pid)
                    latest_id = max(latest_id, pid)
                    newest = max(newest, post['date'])
                    if post['post'].lower() in seen:
                        continue
                    seen.add(post['post'].lower())
                    # Недоступный текст (например, медиа) не считается удалением объявления.
                    if post['parts']:
                        observed.add(('https://t.me/' + post['post']).lower())
                        found = jobs_from_post(post, source, now)
                        fetched.extend(found)
                        count += sum(not j['closed'] for j in found)
                if min(p['date'] for p in posts) < cutoff:
                    complete = True
                    break
                # Две страницы перекрытия сохраняют обновления и закрытия недавних постов.
                if watermark and page >= 1 and max(ids) <= watermark:
                    complete = True
                    break
                next_before = '?before=' + str(min(ids))
                if next_before == before:
                    break
                before = next_before
                time.sleep(.25)
            succeeded += 1
            message = 'Лента доступна' if newest >= (now - timedelta(days=7)).isoformat() else 'В ленте нет публикаций за последние 7 дней'
            if not complete:
                message += '; достигнут лимит страниц, покрытие неполное'
            ok = True
        except Exception as e:
            ok = False
            message = 'Сбой чтения; прежние объявления сохранены'
            print(ident, type(e).__name__, str(e)[:120])
        statuses.append({'id': ident, 'name': source['name'], 'url': 'https://t.me/' + ident,
                         'ok': ok, 'count': count, 'postsScanned': len(seen), 'pages': pages,
                         'latestPostAt': newest or old_status.get(ident.lower(), {}).get('latestPostAt'),
                         'latestPostId': latest_id if ok else old_status.get(ident.lower(), {}).get('latestPostId', 0),
                         'note': source.get('note', ''), 'reviewedAt': source.get('reviewedAt'), 'message': message})
    jobs = merge_observations(old_jobs, fetched, observed, now)
    clean_now = cleanup_due(previous, now)
    jobs, seen = expire_jobs(jobs, previous, now, prune=clean_now)
    ledger = source_metrics(jobs, previous, now)
    for j in jobs:
        j['pay'] = extract_pay(j['text'])
        j['brief'] = brief(j['text'])
        j['replyContacts'] = (j['contacts'] if j.get('digest') else reply_contacts(j['text'], excluded=[x['url'].split('/')[3] for x in j['sources']]))
    for s in statuses:
        own = [j for j in jobs if not j.get('closed') and any(x['url'].split('/')[3].lower() == s['id'].lower() for x in j['sources'])]
        s['newCount'] = sum(j['id'] not in old_ids for j in own)
        history = [x for x in ledger if s['id'].lower() in x['channels']]
        s['jobs7d'] = len(history)
        s['exclusive7d'] = sum(len(x['channels']) == 1 for x in history)
        s['shared7d'] = sum(len(x['channels']) > 1 for x in history)
        s['jobs24h'] = sum(j['date'] >= (now - timedelta(hours=24)).isoformat() for j in own)
        s['latestJobAt'] = max((j['date'] for j in own), default=None)
    result = {'schemaVersion': 4, 'retentionHours': 72, 'lastCleanupAt': now.isoformat() if clean_now else previous.get('lastCleanupAt'), 'seen': seen, 'sourceLedger': ledger, 'generatedAt': now.isoformat(),
              'lastSuccessAt': now.isoformat() if succeeded else previous.get('lastSuccessAt'),
              'newCount': sum(j['id'] not in old_ids and not j.get('closed') for j in jobs),
              'sources': statuses, 'jobs': jobs}
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    temp.replace(target)
    print(f'Sources OK: {succeeded}/{len(statuses)}; jobs: {len(jobs)}; new: {result["newCount"]}')
    return 0 if succeeded else 1

if __name__ == '__main__':
    raise SystemExit(main())
