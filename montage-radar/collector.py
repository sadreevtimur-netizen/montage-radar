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
    t = text.lower()
    skill = re.search(r'монтаж|рилс|reels|shorts|видеоредактор|video\s*editor', t)
    demand = re.search(r'ищ[уеё]|ищем|нуж[ен]|требуе|ваканси|#даюработу|в команду', t)
    resume = re.search(r'#помогу|#резюме|ищу\s+(?:работу|заказы|клиентов)|предлагаю\s+(?:свои\s+)?услуги', t)
    if re.search(r'^(?:[\W\d]*)(?:делаю\s+монтаж|монтирую|я\s+(?:видео)?монтаж[её]р)', t):
        resume = True
    return bool(skill and demand and not resume)

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
    text = ''.join(post['parts']).strip()
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
            'formats': formats or ['Монтаж'], 'pay': amounts[:3], 'contacts': contacts(text, post['links']),
            'risks': inspect_risks(text), 'sources': [{'name': source['name'], 'url': 'https://t.me/' + post['post']}]}

def deduplicate(jobs):
    groups = {}
    for job in sorted(jobs, key=lambda j: (datetime.fromisoformat(j['date']), j.get('checkedAt', '')), reverse=True):
        key = normalize(job['text'])
        # Дословные и близкие перепосты: общий контакт + совпадение слов >= 90%.
        match = key if key in groups else None
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT / 'site/data/jobs.json'))
    args = parser.parse_args()
    target = Path(args.output)
    previous = json.loads(target.read_text('utf-8')) if target.exists() else {'jobs': [], 'lastSuccessAt': None}
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=30)).isoformat()
    jobs = [j for j in previous['jobs'] if j['date'] >= cutoff and is_job(j['text'])]
    statuses, succeeded = [], 0
    for source in json.loads((ROOT / 'sources.json').read_text('utf-8')):
        if not source.get('enabled'):
            continue
        ident = source['id']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{3,31}', ident):
            raise ValueError('Invalid source ID')
        count, before = 0, ''
        try:
            for page in range(3):
                feed = FeedParser()
                feed.feed(fetch('https://t.me/s/' + ident + before))
                posts = [p for p in feed.posts if p['date'] and p['parts']]
                if not posts:
                    if page == 0:
                        raise RuntimeError('Публичная лента не отдала сообщения')
                    break
                fresh = [j for p in posts if (j := make_job(p, source, now))]
                jobs.extend(fresh)
                count += len(fresh)
                ids = [int(p['post'].rsplit('/', 1)[-1]) for p in posts]
                if min(p['date'] for p in posts) < cutoff:
                    break
                before = '?before=' + str(min(ids))
                time.sleep(1)
            succeeded += 1
            statuses.append({'name': source['name'], 'url': 'https://t.me/' + ident, 'ok': True, 'count': count, 'message': 'Проверена открытая лента (до 3 страниц)'})
        except Exception as e:
            statuses.append({'name': source['name'], 'url': 'https://t.me/' + ident, 'ok': False, 'count': count, 'message': 'Источник недоступен; сохранены прежние объявления'})
            print(ident, type(e).__name__, str(e)[:120])
    result = {'generatedAt': now.isoformat(), 'lastSuccessAt': now.isoformat() if succeeded else previous.get('lastSuccessAt'),
              'sources': statuses, 'jobs': deduplicate(jobs)}
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    temp.replace(target)
    print(f'Sources OK: {succeeded}/{len(statuses)}; jobs: {len(result["jobs"])}')
    # Старые данные остаются, но GitHub явно сообщает о полном сбое сбора.
    return 0 if succeeded else 1

if __name__ == '__main__':
    raise SystemExit(main())
