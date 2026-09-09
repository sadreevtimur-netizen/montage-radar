import unittest
from collector import FeedParser, is_job, inspect_risks, deduplicate

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

if __name__=='__main__':unittest.main()
