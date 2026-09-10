import unittest
from collector import FeedParser, is_job, inspect_risks, deduplicate, merge_observations, is_closed, work_flags, expire_jobs, brief, reply_contacts, source_metrics
from datetime import datetime, timezone

class Rules(unittest.TestCase):
    def test_resume_not_job(self):
        self.assertFalse(is_job('Я монтажёр, ищу работу. #резюме'))
        self.assertFalse(is_job('Делаю монтаж Reels/Shorts. Пишите в ЛС. Больше вакансий в боте'))
        self.assertTrue(is_job('Ищем монтажёра YouTube, оплата 5000 рублей'))
    def test_risk_and_negation(self):
        self.assertTrue(inspect_risks('Внесите залог перед началом работы'))
        self.assertFalse(inspect_risks('Не нужно оплачивать доступ. Никогда не присылайте код входа.'))
        self.assertTrue(inspect_risks('Пришлите код входа в Telegram'))
    def test_nested_markup_and_safe_text(self):
        p=FeedParser();p.feed('<div data-post="sample/12"><div class="tgme_widget_message_text">Ищем <b>монтажёра</b><br>Текст &lt;script&gt;</div><time datetime="2026-09-08T12:00:00+00:00"></time><span>999 views</span></div>')
        self.assertEqual(''.join(p.posts[0]['parts']),'Ищем монтажёра\nТекст <script>')
        self.assertTrue(p.posts[0]['date'])
    def test_duplicates(self):
        a={'date':'2026-09-08','text':'Ищем монтажёра, оплата 5000 рублей','contacts':['@demo'],'sources':[{'url':'a'}]}
        b={**a,'sources':[{'url':'b'}]}
        out=deduplicate([a,b]);self.assertEqual(len(out),1);self.assertEqual(len(out[0]['sources']),2)

    def test_real_noise_patterns(self):
        self.assertFalse(is_job('SMM-специалист. Мой опыт работы: монтаж Reels. Больше вакансий тут @somebot'))
        self.assertFalse(is_job('Требуется сценарист YouTube. Прописывать монтажные вставки.'))
        self.assertFalse(is_job('#портфолио Видеомонтажер. Какой проект ищу: Reels.'))
        self.assertFalse(is_job('Меня зовут Виктория, я 2D/3D motion designer. Рассматриваю проектные задачи.'))
        self.assertTrue(is_job('Вакансия: Монтажёр / VFX. Работа удалённая.'))
        self.assertTrue(is_job('Ищем Motion Designer для видео.'))
        self.assertTrue(is_job('Ищем видеомонтажёра YouTube о CS2.'))

    def test_closed_edit_replaces_cached_job(self):
        old={'id':'old','date':'2026-09-08','firstSeenAt':'2026-09-08','text':'Ищем монтажера','contacts':['@demo'],'sources':[{'url':'https://t.me/demo/1'}]}
        fresh={**old,'firstSeenAt':'2026-09-09','closed':True,'text':'Ищем монтажера. Поиск остановлен'}
        out=merge_observations([old],[fresh],{'https://t.me/demo/1'},datetime.now(timezone.utc))
        self.assertEqual(len(out),1)
        self.assertTrue(out[0]['closed'])
        self.assertEqual(out[0]['firstSeenAt'],'2026-09-08')

    def test_repeat_keeps_id_and_original_date(self):
        old={'id':'stable','date':'2026-09-08','firstSeenAt':'2026-09-08','text':'Ищем монтажера YouTube. Оплата 5000','contacts':['@demo'],'sources':[{'url':'a'}]}
        repost={**old,'id':'new','date':'2026-09-10','firstSeenAt':'2026-09-10','sources':[{'url':'b'}]}
        out=deduplicate([old,repost])
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['id'],'stable')
        self.assertEqual(out[0]['date'],'2026-09-08')

    def test_different_clients_not_collapsed(self):
        a={'id':'a','date':'2026-09-08','text':'Ищем монтажера YouTube','contacts':['@one'],'sources':[{'url':'a'}]}
        b={**a,'id':'b','contacts':['@two'],'sources':[{'url':'b'}]}
        self.assertEqual(len(deduplicate([a,b])),2)

    def test_filming_and_closure(self):
        self.assertIn('Нужна съёмка',work_flags('Задачи: Съемка видео для соцсетей'))
        self.assertNotIn('Нужна съёмка',work_flags('Снимать не нужно, исходники предоставим'))
        self.assertTrue(is_closed('Вакансия закрыта'))

    def test_expiry_and_repost_after_expiry(self):
        now=datetime(2026,9,10,12,tzinfo=timezone.utc)
        def job(ident,date):
            return {'id':ident,'date':date,'text':'Ищем монтажера '+ident,'contacts':['@client'],'closed':False}
        old=job('old','2026-09-09T12:00:00+00:00')
        fresh=job('fresh','2026-09-09T12:00:01+00:00')
        closed={**job('closed','2026-09-10T11:00:00+00:00'),'closed':True}
        active,history=expire_jobs([old,fresh,closed],{},now)
        self.assertEqual([j['id'] for j in active],['fresh'])
        self.assertTrue(all('text' not in h for h in history))
        repost={**old,'id':'newpost','date':'2026-09-10T11:00:00+00:00'}
        active,_=expire_jobs([repost],{'seen':history},now)
        self.assertEqual(active,[])

class Improvements(unittest.TestCase):
    def test_primary_role_and_courses(self):
        self.assertFalse(is_job('Ищем SMM-специалиста. Требуется монтажерский опыт и монтаж Reels.'))
        self.assertFalse(is_job('Курс по монтажу. Ищем монтажеров на обучение.'))
        self.assertTrue(is_job('Ищем монтажера. Бюджет обсудим лично.'))
        self.assertTrue(is_job('Ищем монтажера. Работа с нашим SMM-специалистом.'))
    def test_literal_summary(self):
        b=brief('Ищем монтажера YouTube\nОбъем: 10 коротких роликов\nСрок: до 15.09')
        self.assertEqual(b['volume'],'Объем: 10 коротких роликов')
        self.assertEqual(b['deadline'],'Срок: до 15.09')
        self.assertIsNone(brief('Ищем монтажера')['deadline'])
    def test_explicit_contacts(self):
        text='Наш канал @agency\nПортфолио @editor\nОтклик:\n@client_name\nРеклама: пишите @admanager'
        self.assertEqual(reply_contacts(text),['@client_name'])
        self.assertEqual(reply_contacts('Пишите jobs@example.com'),['jobs@example.com'])
        self.assertEqual(reply_contacts('Пример: @random'),[])
    def test_weekly_unique_stats(self):
        now=datetime(2026,9,10,12,tzinfo=timezone.utc)
        j={'id':'one','date':'2026-09-10T10:00:00+00:00','sources':[{'url':'https://t.me/a/1'},{'url':'https://t.me/b/2'}]}
        first=source_metrics([j],{},now)
        second=source_metrics([j],{'sourceLedger':first},now)
        self.assertEqual(len(second),1)
        self.assertEqual(second[0]['channels'],['a','b'])

if __name__=='__main__':unittest.main()
