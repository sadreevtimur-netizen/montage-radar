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
    if re.search(r'#(?:резюме|портфолио|помогу)\b|какой проект ищу|ищу\s+(?:(?:проектную|удаленную|постоянную)\s+)?(?:работу|заказы|клиентов)|предлагаю\s+(?:свои\s+)?услуги|я\s+(?:видео)?монтажер\b', t):
        return False
    role = r'(?:видео)?монтаж[её]р\w*|режиссер\w*\s+монтажа|видеоредактор\w*|video\s*editor|моуш[ен]*[ -]?дизайнер\w*|motion[ -]?designer|рилс[ -]?мейкер\w*|reels[ -]?мейкер\w*'
    if re.search(rf'\bя\s+(?:(?:2d|3d|2d/3d|опытный|начинающий)\s+)?(?:{role})', t[:350]):
        return False
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
    amounts = re.findall(r'(?:от\s*)?\d[\d\s.,]*(?:[–—-]\s*\d[\d\s.,]*)?\s*(?:₽|руб\w*|\$|€|тыс\.?\s*(?:₽|руб\w*)?)[^\n.!?]{0,40}', text, re.I)
    lines = [re.sub(r'#\w+', '', x).strip(' •—-') for x in text.splitlines() if x.strip()]
    title = next((x for x in lines if len(x) > 15 and not x.startswith('#')), 'Вакансия монтажёра')[:140]
    return {'id': hashlib.sha256(post['post'].encode()).hexdigest()[:16], 'title': title,
            'text': text[:14000], 'date': date.isoformat(), 'checkedAt': now.isoformat(),
            'firstSeenAt': now.isoformat(), 'closed': is_closed(text), 'flags': work_flags(text),
            'formats': formats or ['Монтаж'], 'pay': amounts[:3], 'contacts': [c for c in contacts(text, post['links']) if c.lower() != '@' + source['id'].lower() and not (c.startswith('@') and c.lower().endswith('bot'))],
            'risks': inspect_risks(text), 'sources': [{'name': source['name'], 'url': 'https://t.me/' + post['post']}]}

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
                if set(job['contacts']) & set(other['contacts']):
                    b = set(k.split())
                    if len(a & b) / max(1, len(a | b)) >= .9:
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
        old = next((by_url[s['url'].lower()] for s in job['sources'] if s['url'].lower() in by_url), None)
        if old:
            job['id'] = old['id']
            job['firstSeenAt'] = old.get('firstSeenAt', old['date'])
        kept.append(job)
    return sorted(deduplicate(kept), key=lambda j: j['date'], reverse=True)


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
                        job = make_job(post, source, now)
                        if job:
                            fetched.append(job)
                            count += not job['closed']
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
    for s in statuses:
        own = [j for j in jobs if not j.get('closed') and any(x['url'].split('/')[3].lower() == s['id'].lower() for x in j['sources'])]
        s['newCount'] = sum(j['id'] not in old_ids for j in own)
        s['jobs7d'] = sum(j['date'] >= (now - timedelta(days=7)).isoformat() for j in own)
        s['jobs24h'] = sum(j['date'] >= (now - timedelta(hours=24)).isoformat() for j in own)
        s['latestJobAt'] = max((j['date'] for j in own), default=None)
    result = {'schemaVersion': 2, 'generatedAt': now.isoformat(),
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
