"""Research-directory regressions that would misroute actual IR enquiries."""
import importlib.util
import io
import json
import tempfile
import threading
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "research_ir_universe.py"
SPEC = importlib.util.spec_from_file_location("contact_research", SCRIPT)
research = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(research)
except ModuleNotFoundError:
    research = None


class FakeClock:
    def __init__(self):
        self.tick = 0.0
        self.lock = threading.Lock()

    def monotonic(self):
        with self.lock:
            return self.tick

    def advance(self, seconds):
        with self.lock:
            self.tick += max(0.0, seconds)

    def iso(self):
        return (datetime(2026, 10, 11, tzinfo=timezone.utc) + timedelta(seconds=self.monotonic())).isoformat()

    def wait(self, fetcher, seconds):
        if not fetcher.environment_failed.is_set():
            self.advance(seconds)
        return fetcher.environment_failed.is_set()


@unittest.skipIf(research is None, "public research requires the optional data environment")
class ContactResearchTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        for patcher in (
            patch.object(research.time, "monotonic", self.clock.monotonic),
            patch.object(research, "now", self.clock.iso),
            patch.object(research.Fetcher, "wait_for_delay", autospec=True, side_effect=self.clock.wait),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def page(self, html, url="https://company.example/contact/"):
        parser = research.Page()
        parser.feed(html)
        return {"requested_url": url, "url": url, "http_status": 200, **parser.extract(url)}

    def fields(self, text=""):
        return '<form>' + text + '<input type="email" name="email"><textarea name="message"></textarea></form>'

    def robots_parser(self, lines):
        return research.parse_robots(lines)

    def test_actual_6383_literal_allow_permits_only_its_observed_path_without_network(self):
        # Exact body of saved 6383/20261011T173437506705Z/04.json nested robots.
        rules = ("User-agent: *\nDisallow: /\nAllow: /products_jp\nAllow: /after_salesservices_jp\n"
                 "Allow: /others_jp\nAllow: /supplier\nAllow: /training\nAllow: /products_en\n"
                 "Allow: /after_salesservices_en\nAllow: /others_en\nAllow: /newsletter_input\n"
                 "Allow: /member/login\nAllow: /logimat_2024")
        target = "https://inquiry.daifuku.com/others_jp"
        parser = self.robots_parser(rules)
        self.assertFalse(parser.can_fetch(research.USER_AGENT, target))
        self.assertTrue(research.robots_can_fetch(parser, research.USER_AGENT, target))
        self.assertTrue(research.robots_specific_allow_correction(parser, research.USER_AGENT, target))
        self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target.replace("others_jp", "private")))
        fetcher = research.Fetcher()
        original = {"http_status": 200, "text": rules, "url": "https://inquiry.daifuku.com/robots.txt"}
        fetcher.robots["https://inquiry.daifuku.com"] = (parser, original)
        with patch.object(research.requests, "get", side_effect=AssertionError("external GET forbidden")), \
                patch.object(fetcher, "raw_get", return_value={"http_status": 200, "url": target}) as body:
            captured = fetcher.capture_one(target)
        body.assert_called_once_with(target)
        self.assertIs(original, captured["robots"])
        self.assertEqual(200, captured["http_status"])
        self.assertEqual(0, fetcher.http_get_attempt_count)

    def test_literal_robots_rule_order_ties_and_narrower_denial(self):
        target = "https://issuer.invalid/ir/private/ask"
        for lines in ("Disallow: /\nAllow: /ir/\nDisallow: /ir/private/",
                      "Disallow: /ir/private/\nDisallow: /\nAllow: /ir/",
                      "Allow: /ir/\nDisallow: /ir/private/\nDisallow: /"):
            with self.subTest(lines=lines):
                parser = self.robots_parser("User-agent: *\n" + lines)
                self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))
                self.assertTrue(research.robots_can_fetch(parser, research.USER_AGENT, target.replace("private/ask", "public/ask")))
        for lines in ("Disallow: /ir/\nAllow: /ir/", "Allow: /ir/\nDisallow: /ir/"):
            parser = self.robots_parser("User-agent: *\n" + lines)
            self.assertTrue(research.robots_can_fetch(parser, research.USER_AGENT, target))
            self.assertFalse(research.robots_specific_allow_correction(parser, research.USER_AGENT, target))

    def test_literal_robots_preserves_existing_useragent_group_selection(self):
        target = "https://issuer.invalid/ir/ask"
        parser = self.robots_parser("User-agent: ir-agent\nDisallow: /\n\nUser-agent: *\nDisallow: /\nAllow: /ir/")
        self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))
        self.assertTrue(research.robots_can_fetch(parser, "unrelated-bot/1", target))
        # Stdlib chooses the FIRST matching non-default group, not a new merge.
        parser = self.robots_parser("User-agent: ir-agent\nDisallow: /\n\nUser-agent: ir-agent-public-research\nAllow: /ir/")
        self.assertEqual(parser.can_fetch(research.USER_AGENT, target),
                         research.robots_can_fetch(parser, research.USER_AGENT, target))

    def test_literal_robots_keeps_stdlib_percent_params_query_normalization(self):
        parser = self.robots_parser("User-agent: *\nDisallow: /\nAllow: /IR情報/\nDisallow: /IR情報/private\nAllow: /ir;ask?kind=IR")
        for target in ("https://issuer.invalid/IR情報/ask", "https://issuer.invalid/IR%E6%83%85%E5%A0%B1/ask",
                       "https://issuer.invalid/ir;ask?kind=IR&more=1", "https://issuer.invalid/%69r;ask?kind=IR"):
            with self.subTest(target=target):
                self.assertTrue(research.robots_can_fetch(parser, research.USER_AGENT, target))
        for target in ("https://issuer.invalid/IR情報/private", "https://issuer.invalid/ir;ask?kind=product"):
            self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))

    def test_pattern_guard_never_promotes_legacy_denials_or_saved_corrections(self):
        target = "https://issuer.invalid/ir/private"
        for pattern in ("/ir/*", "/ir/private$", "/other%2A", "/ir/%24"):
            with self.subTest(pattern=pattern):
                parser = self.robots_parser("User-agent: *\nDisallow: /\nAllow: /ir/\nDisallow: " + pattern)
                self.assertFalse(parser.can_fetch(research.USER_AGENT, target))
                self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))
                self.assertFalse(research.robots_specific_allow_correction(parser, research.USER_AGENT, target))
        parser = research.RobotFileParser()
        self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))
        parser.allow_all = True
        self.assertTrue(research.robots_can_fetch(parser, research.USER_AGENT, target))
        parser.disallow_all = True
        self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))
        self.assertFalse(research.robots_specific_allow_correction(parser, research.USER_AGENT, target))

    def test_anchor_valueless_title_preserves_visible_text_without_ir_promotion(self):
        for attribute, expected in (("title", "公開窓口"), ('title=""', "公開窓口"),
                                    ('title="会社窓口"', "会社窓口 公開窓口")):
            with self.subTest(attribute=attribute):
                page = self.page(f'<title>お問い合わせ</title><a href="/contact/" {attribute}>'
                                 '<img alt="公開窓口"></a> IR情報')
                self.assertEqual(expected, page["links"][0]["label"])
                self.assertEqual("/contact/", page["links"][0]["href"])
                self.assertEqual("none", research.analyze_page(page)["level"])
        page = self.page('<a href="/questions" title>株式・IR</a>')
        self.assertEqual("株式・IR", page["links"][0]["label"])
        self.assertEqual("none", research.analyze_page(page)["level"])

    def test_html_base_resolves_links_and_frames_and_preserves_attribute_values(self):
        page = self.page('<base href="https://issuer.invalid/">'
                         '<a href="ir/contact/?kind=IR&amp;view=1#questions">IRお問い合わせ</a>'
                         '<iframe src="forms/ir.html"></iframe>', 'https://issuer.invalid/ir/')
        self.assertEqual('https://issuer.invalid/', page['base_url'])
        self.assertEqual('https://issuer.invalid/', page['base_href'])
        self.assertEqual(['https://issuer.invalid/'], page['base_hrefs'])
        self.assertEqual('https://issuer.invalid/ir/contact/?kind=IR&view=1#questions', page['links'][0]['url'])
        self.assertEqual('ir/contact/?kind=IR&view=1#questions', page['links'][0]['href'])
        self.assertEqual('https://issuer.invalid/forms/ir.html', page['links'][1]['url'])
        self.assertEqual('forms/ir.html', page['links'][1]['src'])

    def test_first_href_base_wins_without_chaining_later_bases(self):
        page = self.page('<base href="../"><base href="https://other.invalid/ignored/">'
                         '<a href="ir/contact/">IRお問い合わせ</a>', 'https://issuer.invalid/company/about/')
        self.assertEqual('../', page['base_href'])
        self.assertEqual(['../', 'https://other.invalid/ignored/'], page['base_hrefs'])
        self.assertEqual('https://issuer.invalid/company/', page['base_url'])
        self.assertEqual('https://issuer.invalid/company/ir/contact/', page['links'][0]['url'])

    def test_invalid_first_base_never_selects_later_base_or_invents_relative_http_urls(self):
        for href in ('javascript:alert(1)', 'data:text/html,example', 'mailto:ir@issuer.invalid', 'https://[broken/'):
            with self.subTest(href=href):
                page = self.page(f'<base href="{href}"><base href="/">'
                                 '<a href="contact/">IRお問い合わせ</a>'
                                 '<a href="https://forms.invalid/ir">IRフォーム</a>'
                                 '<a href="mailto:ir@issuer.invalid?subject=IR">IRメール</a>',
                                 'https://issuer.invalid/ir/')
                self.assertEqual([href, '/'], page['base_hrefs'])
                self.assertEqual(href, page['base_href'])
                self.assertIsNone(page['base_url'])
                self.assertTrue(page['base_resolution_error'])
                self.assertEqual('contact/', page['unresolved_links'][0]['href'])
                self.assertEqual('base_url_unresolved', page['unresolved_links'][0]['resolution_error'])
                self.assertEqual('https://forms.invalid/ir', page['links'][0]['url'])
                self.assertEqual('mailto:ir@issuer.invalid?subject=IR', page['links'][1]['url'])

    def test_opaque_base_retains_relative_href_but_does_not_put_it_in_candidate_links(self):
        page = self.page('<base target="_blank"><base href="data:text/plain,example">'
                         '<a href="questions/?kind=IR">IRお問い合わせ</a>'
                         '<a href="mailto:ir@issuer.invalid">IRメール</a>', 'https://issuer.invalid/ir/')
        self.assertEqual('data:text/plain,example', page['base_href'])
        self.assertIsNone(page['base_url'])
        self.assertEqual(['data:text/plain,example'], page['base_hrefs'])
        self.assertEqual('questions/?kind=IR', page['unresolved_links'][0]['href'])
        self.assertEqual('mailto:ir@issuer.invalid', page['links'][0]['href'])
        self.assertEqual([], research.candidate_links(page, 'issuer.invalid', True))

    def test_without_base_href_links_use_the_final_document_url(self):
        page = self.page('<base target="_blank"><a href="questions/?kind=IR">IRお問い合わせ</a>',
                         'https://issuer.invalid/ir/')
        self.assertIsNone(page['base_href'])
        self.assertEqual([], page['base_hrefs'])
        self.assertIsNone(page['base_resolution_error'])
        self.assertEqual([], page['unresolved_links'])
        self.assertEqual('https://issuer.invalid/ir/questions/?kind=IR', page['links'][0]['url'])

    def test_bare_base_href_counts_as_first_empty_href(self):
        page = self.page('<base href><base href="https://other.invalid/">'
                         '<a href="questions/">IRお問い合わせ</a>', 'https://issuer.invalid/ir/')
        self.assertEqual('', page['base_href'])
        self.assertEqual(['', 'https://other.invalid/'], page['base_hrefs'])
        self.assertEqual('https://issuer.invalid/ir/questions/', page['links'][0]['url'])

    def test_empty_base_is_valid_and_protocol_relative_base_retains_https(self):
        for base_href, expected_base, expected_link in (
            ('', 'https://issuer.invalid/ir/index.html', 'https://issuer.invalid/ir/contact/'),
            ('//forms.invalid/public/', 'https://forms.invalid/public/', 'https://forms.invalid/public/contact/'),
        ):
            with self.subTest(base_href=base_href):
                page = self.page(f'<base href="{base_href}"><base href="/ignored/">'
                                 '<a href="contact/">IRお問い合わせ</a>', 'https://issuer.invalid/ir/index.html')
                self.assertEqual(base_href, page['base_href'])
                self.assertEqual(expected_base, page['base_url'])
                self.assertEqual(expected_link, page['links'][0]['url'])

    def test_relative_html_base_uses_final_document_after_http_redirect(self):
        fetcher = research.Fetcher(delay=1)
        attempted = []

        def response(url, **kwargs):
            attempted.append(url)
            if url.endswith('/robots.txt'):
                return self.response(url, 404, '')
            if url == 'https://old.invalid/ir/':
                value = self.response(url, 302, '')
                value.headers['Location'] = 'https://new.invalid/company/ir/'
                return value
            self.assertEqual('https://new.invalid/company/ir/', url)
            return self.response(url, 200, '<base href="../"><a href="contact/ir/">IRお問い合わせ</a>')

        with patch.object(research.requests, 'get', side_effect=response):
            captured = fetcher.capture('https://old.invalid/ir/')
        self.assertEqual(['https://old.invalid/robots.txt', 'https://old.invalid/ir/',
                          'https://new.invalid/robots.txt', 'https://new.invalid/company/ir/'], attempted)
        self.assertEqual('https://old.invalid/ir/', captured['requested_url'])
        self.assertEqual('https://new.invalid/company/ir/', captured['url'])
        self.assertEqual('https://new.invalid/company/', captured['base_url'])
        self.assertEqual('https://new.invalid/company/contact/ir/', captured['links'][0]['url'])

    def test_http_shift_jis_charset_precedes_conflicting_utf8_meta(self):
        # Saved 2784 external IR form had HTTP Shift_JIS, selected UTF-8 and
        # 1190 replacement characters. Original bytes are not modified/recovered.
        html = '<meta charset="UTF-8"><title>IRお問い合わせ</title>投資家の皆様' + self.fields()
        value = self.response('https://forms.invalid/ir', 200, '')
        value.headers['Content-Type'] = 'text/html;charset=Shift_JIS'
        value.encoding = 'Shift_JIS'
        value.iter_content.return_value = [html.encode('cp932')]
        with patch.object(research.requests, 'get', return_value=value):
            captured = research.Fetcher().raw_get(value.url)
        self.assertEqual('cp932', captured['encoding'])
        self.assertEqual('http_charset', captured['encoding_source'])
        self.assertEqual('shift_jis', captured['http_charset'])
        self.assertEqual('UTF-8', captured['html_meta_charset'])
        self.assertEqual('IRお問い合わせ', captured['title'])
        self.assertNotIn('\ufffd', captured['text'])
        self.assertEqual('form_fields_verified', research.analyze_page(captured)['level'])

    def test_http_utf8_charset_precedes_conflicting_shift_jis_meta(self):
        value = self.response('https://forms.invalid/ir', 200,
                              '<meta charset="Shift_JIS"><title>IRお問い合わせ</title>')
        value.headers['Content-Type'] = 'text/html; Charset="UTF-8"'
        with patch.object(research.requests, 'get', return_value=value):
            captured = research.Fetcher().raw_get(value.url)
        self.assertEqual('utf-8', captured['encoding'])
        self.assertEqual('http_charset', captured['encoding_source'])
        self.assertEqual('IRお問い合わせ', captured['title'])
        self.assertNotIn('\ufffd', captured['text'])

    def test_html_meta_is_used_when_http_charset_is_absent(self):
        value = self.response('https://forms.invalid/ir', 200, '')
        value.encoding = 'ISO-8859-1'  # requests' text/html default, not a declaration.
        value.iter_content.return_value = ['<meta charset="Shift_JIS"><title>IRお問い合わせ</title>'.encode('cp932')]
        with patch.object(research.requests, 'get', return_value=value):
            captured = research.Fetcher().raw_get(value.url)
        self.assertEqual('cp932', captured['encoding'])
        self.assertEqual('html_meta_charset', captured['encoding_source'])
        self.assertIsNone(captured['http_charset'])
        self.assertEqual('IRお問い合わせ', captured['title'])

    def test_default_latin1_is_not_confused_with_explicit_http_charset(self):
        for header, body, expected, source in (
            ('text/html', '<title>IRお問い合わせ</title>'.encode('utf-8'), 'IRお問い合わせ', 'utf8_fallback'),
            ('text/html; charset=ISO-8859-1', b'<meta charset="UTF-8"><title>caf\xe9</title>', 'café', 'http_charset'),
        ):
            with self.subTest(header=header):
                value = self.response('https://forms.invalid/ir', 200, '')
                value.headers['Content-Type'] = header
                value.encoding = 'ISO-8859-1'
                value.iter_content.return_value = [body]
                with patch.object(research.requests, 'get', return_value=value):
                    captured = research.Fetcher().raw_get(value.url)
                self.assertEqual(source, captured['encoding_source'])
                self.assertEqual(expected, captured['title'])

    def test_http_equiv_meta_charset_remains_supported_without_header_charset(self):
        value = self.response('https://forms.invalid/ir', 200, '')
        value.iter_content.return_value = [('<meta http-equiv="Content-Type" content="text/html; charset=Shift_JIS">'
                                           '<title>IRお問い合わせ</title>').encode('cp932')]
        with patch.object(research.requests, 'get', return_value=value):
            captured = research.Fetcher().raw_get(value.url)
        self.assertEqual('html_meta_charset', captured['encoding_source'])
        self.assertEqual('cp932', captured['encoding'])
        self.assertEqual('IRお問い合わせ', captured['title'])

    def test_invalid_http_charset_does_not_silently_fall_back_to_meta(self):
        value = self.response('https://forms.invalid/ir', 200, '<meta charset="UTF-8"><title>IRお問い合わせ</title>')
        value.headers['Content-Type'] = 'text/html; charset=invalid-test-codec'
        with patch.object(research.requests, 'get', return_value=value):
            captured = research.Fetcher().raw_get(value.url)
        self.assertEqual('LookupError', captured['error'])
        self.assertEqual('http_charset', captured['encoding_source'])
        self.assertEqual('invalid-test-codec', captured['encoding'])
        self.assertIsNotNone(captured['http_get_completed_at'])
        value.__exit__.assert_called_once()

    def test_japanese_ir_heading_is_not_lost_to_unicode_word_boundary(self):
        page = self.page('<title>IRに関するお問い合わせ</title>' + self.fields())
        self.assertEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_english_ir_form_heading(self):
        page = self.page('<title>IR Inquiries</title>' + self.fields())
        self.assertEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_euglena_ir_form_with_plain_mail_fields_is_verified(self):
        # Saved 2931 /contact/b06/ and /contact/c03/ controls use text mail/mail2
        # and textarea comment, beneath an explicit corporate/individual IR title.
        form = ('<form>お名前 必須<input type="text" name="name">'
                '電話番号<input type="text" name="tel">'
                'メールアドレス 必須<input type="text" name="mail">'
                'メールアドレス（確認用） 必須<input type="text" name="mail2">'
                '会社名<input type="text" name="corp">'
                'お問い合わせの内容 必須<textarea name="comment"></textarea>'
                '<input type="checkbox" name="agree"></form>')
        for audience, route in (("法人", "b06"), ("個人", "c03")):
            with self.subTest(audience=audience):
                page = self.page(
                    f'<title>株式・IRに関するお問い合わせ（{audience}のお客様） | 株式会社ユーグレナ</title>' + form,
                    f'https://www.euglena.jp/contact/{route}/',
                )
                self.assertEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_plain_mail_and_existing_email_names_ignore_case(self):
        for name in ("mail", "Mail", "MAIL2", "EMAIL"):
            with self.subTest(name=name):
                page = self.page('<title>IRお問い合わせ</title><form>'
                                 f'<input type="text" name="{name}">'
                                 '<textarea name="comment"></textarea></form>')
                self.assertEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_plain_mail_fields_still_require_ir_form_scope(self):
        fields = '<input type="text" name="mail"><textarea name="comment"></textarea>'
        for html in (
            '<title>お問い合わせ</title><nav>IR情報 お問い合わせ</nav><form>商品のお問い合わせ' + fields + '</form>',
            '<title>お問い合わせ</title><form>事業・商品について その他 個人情報保護方針 株主や投資家の皆様への情報提供' + fields + '</form>',
        ):
            with self.subTest(html=html):
                page = self.page(html)
                self.assertTrue(research.form_has_fields(page["forms"][0]))
                self.assertEqual("none", research.analyze_page(page)["level"])

    def test_non_reply_controls_named_mail_are_not_email_inputs(self):
        for control in ('<input type="search" name="mail">',
                        '<input type="checkbox" name="mail">',
                        '<select name="mail"><option>IRについて</option></select>'):
            with self.subTest(control=control):
                page = self.page('<title>IRお問い合わせ</title><form>' + control +
                                 '<textarea name="comment"></textarea></form>')
                self.assertFalse(research.form_has_fields(page["forms"][0]))
                self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_mail_and_question_must_be_distinct_controls_in_one_form(self):
        for forms in ('<form><input type="text" name="mail" placeholder="question"></form>',
                      '<form><input type="text" name="mail"></form><form><textarea name="comment"></textarea></form>'):
            with self.subTest(forms=forms):
                page = self.page('<title>IRお問い合わせ</title>' + forms)
                self.assertFalse(any(research.form_has_fields(f) for f in page["forms"]))
                self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_opaque_email_identifier_requires_manual_review(self):
        # Saved 2962 IR form exposes the email label but uses formElementVal976.
        page = self.page('<title>IRに関するお問い合わせ</title><form>'
                         'メールアドレス 【必須】<input type="text" name="formElementVal976">'
                         'お問い合わせ内容 【必須】<textarea name="formElementVal977"></textarea></form>')
        self.assertFalse(research.form_has_fields(page["forms"][0]))
        self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_ir_navigation_and_customer_form_are_not_ir_acceptance(self):
        page = self.page('<title>お問い合わせ</title><nav>IR情報 お問い合わせ</nav>' + self.fields('商品のお問い合わせ 店舗名'))
        self.assertEqual("none", research.analyze_page(page)["level"])

    def test_privacy_statement_about_investors_is_not_an_ir_form(self):
        page = self.page('<title>お問い合わせ</title>' + self.fields('事業・商品について その他 個人情報保護方針 株主や投資家の皆様への情報提供'))
        self.assertEqual("none", research.analyze_page(page)["level"])

    def test_shareholder_benefits_only_are_not_financial_ir(self):
        page = self.page('<title>株主優待に関するお問い合わせ</title>' + self.fields('株主番号'))
        self.assertEqual("none", research.analyze_page(page)["level"])

    def test_actual_ir_category_in_generic_form_is_valid(self):
        page = self.page('<title>お問い合わせ</title>' + self.fields('お問い合わせ種別 商品について IRについて その他'))
        self.assertEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_ir_telephone_next_to_product_form_does_not_validate_form(self):
        page = self.page('<title>お問い合わせ</title><section>IRのお問い合わせは電話で</section>' + self.fields('製品・店舗のお問い合わせ'))
        self.assertEqual("none", research.analyze_page(page)["level"])

    def test_input_example_address_is_not_a_published_ir_mailbox(self):
        page = self.page('<title>IRお問い合わせ</title>IRお問い合わせ 記入例：xxxxx@company.example')
        self.assertEqual([], research.analyze_page(page)["emails"])

    def test_published_ir_mailbox_is_valid(self):
        page = self.page('<title>IRお問い合わせ</title>IRお問い合わせ E-mail ir@issuer.invalid')
        self.assertEqual(["ir@issuer.invalid"], research.analyze_page(page)["emails"])

    def test_instruction_to_read_ir_page_is_not_acceptance_in_general_form(self):
        page = self.page('<title>お問い合わせ</title>' + self.fields('ご意見ご要望 事業 なお、IR情報については、IRページにて情報を発信しておりますのでそちらをご確認ください。'))
        self.assertEqual("none", research.analyze_page(page)["level"])

    def test_form_authentication_without_question_is_not_verified(self):
        page = self.page('<title>IRお問い合わせ</title><form><input type="email" name="email"></form>')
        self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_checkbox_and_submit_names_do_not_demonstrate_input_fields(self):
        page = self.page('<title>IRお問い合わせ</title><form><input type="checkbox" name="email_updates"><input type="submit" name="message"></form>')
        self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_search_fields_are_not_a_question_form(self):
        page = self.page('<title>IRお問い合わせ</title><form><input type="search" name="email"><input type="search" name="question"></form>')
        self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_single_field_does_not_demonstrate_email_and_question(self):
        page = self.page('<title>IRお問い合わせ</title><form><input name="email_message"></form>')
        self.assertNotEqual("form_fields_verified", research.analyze_page(page)["level"])

    def test_hidden_values_and_example_values_are_not_archived(self):
        page = self.page('<form><input type="hidden" name="nonce" value="token"><input name="email" value="person@example.org"></form>')
        self.assertEqual([{"tag": "input", "name": "email"}], page["forms"][0]["controls"])

    def test_ir_query_is_preserved(self):
        self.assertEqual("https://company.example/contact?type=IR", research.http_url("https://company.example/contact?type=IR#top"))

    def test_robots_server_failure_stops_content_but_other_origin_continues(self):
        for status in (500, 503):
            with self.subTest(status=status):
                fetcher = research.Fetcher()
                attempted = []

                def response(url, **kwargs):
                    attempted.append(url)
                    if url == 'https://failed.invalid/robots.txt':
                        return self.response(url, status, 'upstream unavailable')
                    self.assertNotIn('failed.invalid', url, 'Failed robots must prevent a content GET')
                    return self.response(url, 404 if url.endswith('/robots.txt') else 200, 'public page')

                with patch.object(research.requests, 'get', side_effect=response), redirect_stdout(io.StringIO()):
                    stopped = fetcher.capture('https://failed.invalid/contact/')
                    cached_stop = fetcher.capture('https://failed.invalid/ir/')
                    allowed = fetcher.capture('https://healthy.invalid/contact/')
                self.assertEqual('robots_unreachable_stopped', stopped['error'])
                self.assertFalse(stopped['http_get_attempted'])
                self.assertNotIn('http_status', stopped)
                self.assertEqual(status, stopped['robots']['http_status'])
                self.assertEqual('upstream unavailable', stopped['robots']['text'])
                self.assertTrue(stopped['robots']['http_get_attempted'])
                self.assertEqual(f'http_{status}', stopped['robots']['failure_signature'])
                self.assertEqual('robots_unreachable_stopped', cached_stop['error'])
                self.assertEqual(200, allowed['http_status'])
                self.assertEqual(['https://failed.invalid/robots.txt', 'https://healthy.invalid/robots.txt',
                                  'https://healthy.invalid/contact/'], attempted)
                self.assertEqual(3, fetcher.http_get_attempt_count)
                self.assertFalse(fetcher.environment_failed.is_set())

    def test_robots_transport_exceptions_preserve_failure_without_content_get(self):
        for exception in (research.requests.exceptions.ProxyError, research.requests.exceptions.ReadTimeout, research.requests.exceptions.SSLError):
            with self.subTest(exception=exception):
                fetcher = research.Fetcher()
                with patch.object(research.requests, 'get', side_effect=exception('not retained')) as request:
                    stopped = fetcher.capture('https://issuer.invalid/contact/')
                self.assertEqual('robots_unreachable_stopped', stopped['error'])
                self.assertFalse(stopped['http_get_attempted'])
                self.assertEqual(exception.__name__, stopped['robots']['error'])
                self.assertEqual('request_exception:' + exception.__name__, stopped['robots']['failure_signature'])
                self.assertTrue(stopped['robots']['http_get_attempted'])
                self.assertIsNotNone(stopped['robots']['http_get_completed_at'])
                self.assertNotIn('not retained', json.dumps(stopped))
                self.assertEqual(1, request.call_count)
                self.assertEqual(1, fetcher.http_get_attempt_count)

    def test_unresolved_robots_redirect_stops_before_content_get(self):
        for location in (None, 'mailto:ir@issuer.invalid', 'https://[invalid/'):
            with self.subTest(location=location):
                fetcher = research.Fetcher()
                value = self.response('https://issuer.invalid/robots.txt', 302, 'redirect response')
                if location is not None:
                    value.headers['Location'] = location
                with patch.object(research.requests, 'get', return_value=value) as request:
                    stopped = fetcher.capture('https://issuer.invalid/contact/')
                self.assertEqual('robots_unreachable_stopped', stopped['error'])
                self.assertFalse(stopped['http_get_attempted'])
                self.assertEqual(302, stopped['robots']['http_status'])
                self.assertEqual('redirect response', stopped['robots']['text'])
                self.assertEqual(1, request.call_count)
                self.assertEqual(1, fetcher.http_get_attempt_count)

    def test_robots_redirect_loop_retains_hops_without_repeating_them(self):
        fetcher = research.Fetcher()
        attempted = []

        def response(url, **kwargs):
            attempted.append(url)
            value = self.response(url, 302, 'robots redirect')
            value.headers['Location'] = '/robots-other.txt' if url.endswith('/robots.txt') else '/robots.txt'
            return value

        with patch.object(research.requests, 'get', side_effect=response):
            stopped = fetcher.capture('https://issuer.invalid/contact/')
        self.assertEqual('robots_unreachable_stopped', stopped['error'])
        self.assertEqual('redirect_loop', stopped['robots_failure_reason'])
        self.assertEqual(['https://issuer.invalid/robots.txt', 'https://issuer.invalid/robots-other.txt'], attempted)
        self.assertEqual('robots redirect', stopped['robots']['text'])
        self.assertEqual(1, len(stopped['robots']['redirects']))
        self.assertTrue(stopped['robots']['redirects'][0]['http_get_attempted'])
        self.assertEqual(2, fetcher.http_get_attempt_count)

    def test_robots_redirect_limit_stops_after_five_followed_hops(self):
        fetcher = research.Fetcher()
        attempted = []

        def response(url, **kwargs):
            attempted.append(url)
            self.assertIn('robots', url)
            value = self.response(url, 302, 'robots redirect')
            value.headers['Location'] = '/robots' + str(len(attempted)) + '.txt'
            return value

        with patch.object(research.requests, 'get', side_effect=response):
            stopped = fetcher.capture('https://issuer.invalid/contact/')
        self.assertEqual('robots_unreachable_stopped', stopped['error'])
        self.assertEqual('redirect_limit', stopped['robots_failure_reason'])
        self.assertEqual(6, len(attempted))
        self.assertEqual(5, len(stopped['robots']['redirects']))
        self.assertEqual('https://issuer.invalid/robots6.txt', stopped['robots']['redirect_target'])
        self.assertEqual(6, fetcher.http_get_attempt_count)

    def test_successful_robots_redirect_still_applies_rules_to_original_origin(self):
        fetcher = research.Fetcher()
        attempted = []

        def response(url, **kwargs):
            attempted.append(url)
            if url == 'https://issuer.invalid/robots.txt':
                value = self.response(url, 302, 'robots moved')
                value.headers['Location'] = 'https://robots.invalid/issuer.txt'
                return value
            self.assertEqual('https://robots.invalid/issuer.txt', url)
            value = self.response(url, 200, 'User-agent: *\nDisallow: /contact/\n')
            value.headers['Content-Type'] = 'text/plain; charset=utf-8'
            return value

        with patch.object(research.requests, 'get', side_effect=response):
            stopped = fetcher.capture('https://issuer.invalid/contact/')
        self.assertEqual('robots_disallowed', stopped['error'])
        self.assertEqual(2, len(attempted))
        self.assertEqual(200, stopped['robots']['http_status'])
        self.assertEqual(1, len(stopped['robots']['redirects']))

    def test_absent_robots_404_and_410_allow_content(self):
        for status in (404, 410):
            with self.subTest(status=status):
                fetcher = research.Fetcher()

                def response(url, **kwargs):
                    return self.response(url, status if url.endswith('/robots.txt') else 200, 'public page')

                with patch.object(research.requests, 'get', side_effect=response) as request:
                    captured = fetcher.capture('https://issuer.invalid/contact/')
                self.assertNotIn('error', captured)
                self.assertTrue(captured['http_get_attempted'])
                self.assertEqual(200, captured['http_status'])
                self.assertEqual(status, captured['robots']['http_status'])
                self.assertEqual(2, request.call_count)

    def test_successful_robots_preserves_disallow_and_crawl_delay(self):
        fetcher = research.Fetcher()
        starts = []

        def response(url, **kwargs):
            starts.append((url, self.clock.monotonic()))
            if url.endswith('/robots.txt'):
                value = self.response(url, 200, 'User-agent: *\nDisallow: /private/\nCrawl-delay: 4\n')
                value.headers['Content-Type'] = 'text/plain; charset=utf-8'
                return value
            self.assertEqual('https://issuer.invalid/contact/', url)
            return self.response(url, 200, 'public contact')

        with patch.object(research.requests, 'get', side_effect=response):
            blocked = fetcher.capture('https://issuer.invalid/private/questions')
            allowed = fetcher.capture('https://issuer.invalid/contact/')
        self.assertEqual('robots_disallowed', blocked['error'])
        self.assertEqual(200, allowed['http_status'])
        self.assertEqual(2, len(starts))
        self.assertGreaterEqual(starts[1][1] - starts[0][1], 4)

    def test_robots_401_403_429_remain_access_denied_stops(self):
        for status in (401, 403, 429):
            with self.subTest(status=status):
                fetcher = research.Fetcher()
                value = self.response('https://issuer.invalid/robots.txt', status, 'restricted')
                value.headers['Retry-After'] = '10'
                with patch.object(research.requests, 'get', return_value=value) as request:
                    stopped = fetcher.capture('https://issuer.invalid/contact/')
                self.assertEqual('robots_access_denied_stopped', stopped['error'])
                self.assertFalse(stopped['http_get_attempted'])
                self.assertEqual(status, stopped['robots']['http_status'])
                self.assertEqual(10, stopped['robots']['retry_after_seconds'])
                self.assertEqual(1, request.call_count)

    def test_common_robots_failures_count_once_per_origin_for_global_circuit(self):
        fetcher = research.Fetcher()
        attempted = []
        text = 'Invalid argument|remote address:envoy://cloudflare_https_tunnel/'

        def response(url, **kwargs):
            attempted.append(url)
            self.assertTrue(url.endswith('/robots.txt'))
            return self.response(url, 503, text)

        with patch.object(research.requests, 'get', side_effect=response), redirect_stdout(io.StringIO()):
            stopped = [fetcher.capture(f'https://{name}.invalid/contact/') for name in ('one', 'two', 'three', 'four')]
        self.assertTrue(all(page['error'] == 'robots_unreachable_stopped' for page in stopped))
        self.assertTrue(all(not page['http_get_attempted'] for page in stopped))
        self.assertEqual(3, len(attempted))
        self.assertEqual(3, fetcher.http_get_attempt_count)
        self.assertEqual(3, fetcher.stats()['common_transport_503_count'])
        self.assertTrue(fetcher.environment_failed.is_set())
        self.assertEqual(text, stopped[0]['robots']['text'])
        self.assertEqual('environment_circuit_breaker_open', stopped[3]['robots']['error'])
        self.assertFalse(stopped[3]['robots']['http_get_attempted'])

    def test_nested_robots_transport_failure_stays_unconfirmed_after_reclassification(self):
        for failure in ('common_503', 'tls_503', 'ProxyError', 'ReadTimeout', 'SSLError', 'http_500'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                company = {'security_code': '5001', 'company_name': 'Company5001',
                           'market': 'スタンダード（内国株式）', 'jpx_sector': '情報・通信業'}
                seed = {'official_url': 'https://issuer.invalid/'}
                fetcher = research.Fetcher()

                def response(url, **kwargs):
                    self.assertEqual('https://issuer.invalid/robots.txt', url)
                    if failure.endswith('Error') or failure.endswith('Timeout'):
                        raise getattr(research.requests.exceptions, failure)('not retained')
                    text = ('Invalid argument|remote address:envoy://cloudflare_https_tunnel/' if failure == 'common_503'
                            else 'TLS_error: CERTIFICATE_VERIFY_FAILED' if failure == 'tls_503' else 'server error')
                    return self.response(url, 500 if failure == 'http_500' else 503, text)

                with patch.object(research.requests, 'get', side_effect=response) as request, redirect_stdout(io.StringIO()):
                    record = research.investigation(company, seed, output, fetcher, max_pages=7)
                self.assertEqual(1, request.call_count)
                self.assertEqual('unconfirmed', record['investigation_status'])
                self.assertEqual(0, record['successful_official_page_count'])
                self.assertEqual([], record['channels'])
                self.assertIsNone(record['contact_url'])
                expected = 'access_or_parse_failure' if failure == 'http_500' else 'environment_transport_failure'
                self.assertEqual(expected, record['unconfirmed_reason'])
                snapshot = output / record['fetches'][0]['snapshot']
                original_bytes = snapshot.read_bytes()
                self.assertEqual('robots_unreachable_stopped', json.loads(original_bytes)['error'])
                record_path = output / 'records/5001.json'
                research.write_json(record_path, record)
                with patch.object(research.requests, 'get', side_effect=AssertionError('No reclassification GET')):
                    research.reclassify_saved(output, {'5001': company})
                    summary = research.compile_directory(output, {'5001': company})
                reclassified = json.loads(record_path.read_text())
                self.assertEqual(expected, reclassified['unconfirmed_reason'])
                self.assertEqual(original_bytes, snapshot.read_bytes())
                self.assertEqual(0, summary['official_get_company_count'])
                self.assertEqual(0, summary['companies_with_successful_public_page_this_run'])

    def test_robots_failure_cache_is_rechecked_only_in_new_fetcher_batch(self):
        attempted = []

        def failed(url, **kwargs):
            attempted.append(url)
            return self.response(url, 503, 'service unavailable')

        first = research.Fetcher()
        with patch.object(research.requests, 'get', side_effect=failed), redirect_stdout(io.StringIO()):
            stopped = first.capture('https://issuer.invalid/contact/')
            preserved = json.dumps(stopped['robots'], sort_keys=True)
            first.capture('https://issuer.invalid/ir/')
        self.assertEqual(1, len(attempted))

        def restored(url, **kwargs):
            attempted.append(url)
            return self.response(url, 404 if url.endswith('/robots.txt') else 200, 'public contact')

        with patch.object(research.requests, 'get', side_effect=restored):
            allowed = research.Fetcher().capture('https://issuer.invalid/contact/')
        self.assertEqual(200, allowed['http_status'])
        self.assertEqual(3, len(attempted))
        self.assertEqual(preserved, json.dumps(stopped['robots'], sort_keys=True))

    def test_cross_host_redirect_checks_target_robots_before_page(self):
        fetcher = research.Fetcher(delay=0)
        attempted = []

        def public_get(url):
            attempted.append(url)
            result = {"requested_url": url, "url": url, "retrieved_at": research.now(), "submitted": False}
            if url == "https://target.example/robots.txt":
                return {**result, "http_status": 200, "text": "User-agent: *\nDisallow: /contact\n"}
            if url.endswith("/robots.txt"):
                return {**result, "http_status": 404, "text": ""}
            if url == "https://issuer.example/contact":
                return {**result, "http_status": 302, "redirect_target": "https://target.example/contact"}
            self.fail("A disallowed target page must not be requested")

        with patch.object(fetcher, "raw_get", side_effect=public_get):
            result = fetcher.capture("https://issuer.example/contact")
        self.assertEqual("robots_disallowed", result["error"])
        self.assertEqual("https://issuer.example/contact", result["requested_url"])
        self.assertEqual(1, len(result["redirects"]))
        self.assertNotIn("https://target.example/contact", attempted)

    def test_shared_proxy_failure_stops_requests_after_three_origins(self):
        fetcher = research.Fetcher(delay=0)
        body = b"Invalid argument|remote address:envoy://cloudflare_https_tunnel/"

        def response(url, **kwargs):
            self.assertFalse(kwargs["allow_redirects"])
            value = MagicMock()
            value.__enter__.return_value = value
            value.url, value.status_code, value.encoding = url, 503, "utf-8"
            value.headers = {"Content-Type": "text/plain"}
            value.iter_content.return_value = [body]
            return value

        with patch.object(research.requests, "get", side_effect=response) as request:
            for company in ("one", "two", "three"):
                self.assertEqual(503, fetcher.raw_get(f"https://{company}.example/")["http_status"])
            stopped = fetcher.raw_get("https://four.example/")
        self.assertEqual("environment_circuit_breaker_open", stopped["error"])
        self.assertEqual(3, request.call_count)
        self.assertEqual(3, fetcher.http_get_attempt_count)
        self.assertFalse(stopped["http_get_attempted"])

    def response(self, url, status, body):
        value = MagicMock()
        value.__enter__.return_value = value
        value.url, value.status_code, value.encoding = url, status, "utf-8"
        value.headers = {"Content-Type": "text/html"}
        value.iter_content.return_value = [body.encode("utf-8")]
        return value

    def survey_fixture(self, root, codes, missing=()):
        universe, seeds, output = root / "input.csv", root / "seeds.json", root / "survey"
        companies = [{"security_code": code, "company_name": "Company" + code,
                      "market": "スタンダード（内国株式）", "jpx_sector": "情報・通信業"} for code in codes]
        universe.write_text("security_code,company_name,market,jpx_sector\n" + "".join(
            ",".join(company.values()) + "\n" for company in companies), encoding="utf-8")
        seeds.write_text(json.dumps([{"security_code": code, "official_url": f"https://issuer{code}.invalid/"} for code in codes]))
        originals = {}
        for company in companies:
            code = company["security_code"]
            if code in missing:
                continue
            record = {**company, "investigation_status": "unconfirmed", "verification_level": "none",
                      "outreach_suitability": "unconfirmed", "unconfirmed_reason": "environment_transport_failure",
                      "manual_review_required": True, "evidence": [], "fetches": [], "preserved": "original " + code}
            path = output / "records" / f"{code}.json"
            research.write_json(path, record)
            originals[code] = path.read_bytes()
        argv = [str(SCRIPT), "--universe", str(universe), "--seeds", str(seeds), "--output", str(output),
                "--resume-network-errors", "--workers", "1", "--max-pages", "1"]
        return output, argv, originals

    def test_exception_retains_three_saved_sources_five_company_gets_and_old_attempt(self):
        issuer = "https://issuer1301.invalid"
        pages = {
            issuer + "/": '<title>Company1301</title><a href="/investors" title>IR情報</a>',
            issuer + "/investors": '<title>IR情報 | Company1301</title>'
                '<a href="/investors/contact/" title="">IRお問い合わせ</a>',
            issuer + "/investors/contact/": '<title>IRお問い合わせ</title>Company1301' + self.fields()
                + '<a href="/investors/contact/questions/">IRお問い合わせ</a>',
            issuer + "/investors/contact/questions/": '<html>offline-parser-fault</html>',
        }
        requests_seen = []
        responses = []

        def public_get(url, **kwargs):
            requests_seen.append(url)
            self.clock.advance(1)
            if "www.jpx.co.jp" in url:
                response = self.response(url, 200, "新規上場")
            elif url.endswith("/robots.txt"):
                response = self.response(url, 404, "")
            else:
                response = self.response(url, 200, pages[url])
            responses.append(response)
            return response

        original_feed = research.Page.feed

        def parse_or_fail(parser, data):
            if "offline-parser-fault" in data:
                raise TypeError("offline injected parsing failure")
            return original_feed(parser, data)

        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), ["1301"])
            argv.extend(["--max-pages", "7"])
            old = json.loads(originals["1301"])
            prior = output / "attempts/1301/prior.json"
            research.write_json(prior, {"preserved": "older immutable attempt"})
            prior_bytes = prior.read_bytes()
            old["previous_attempts"] = ["attempts/1301/prior.json"]
            record_path = output / "records/1301.json"
            research.write_json(record_path, old)
            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), \
                    patch.object(research.requests, "get", side_effect=public_get), \
                    patch.object(research.Page, "feed", parse_or_fail), redirect_stdout(stdout):
                self.assertEqual(0, research.main())
            record = json.loads(record_path.read_text())
            run = json.loads(stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual(5, record["http_get_attempt_count"])
            self.assertEqual(5, run["company_http_get_attempt_count"])
            self.assertEqual(6, len(requests_seen))  # Plus one JPX preflight.
            self.assertEqual(3, len(record["fetches"]))
            self.assertEqual(3, record["successful_official_page_count"])
            self.assertEqual(list(pages)[:3], [f["url"] for f in record["fetches"]])
            self.assertEqual("unconfirmed", record["investigation_status"])
            self.assertEqual("none", record["verification_level"])
            self.assertEqual("not_stated", record["individual_access"])
            self.assertEqual("unconfirmed", record["outreach_suitability"])
            self.assertEqual("investigation_exception", record["unconfirmed_reason"])
            self.assertIsNone(record["contact_url"])
            self.assertEqual([], record["channels"])
            self.assertEqual([], record["public_ir_emails"])
            self.assertEqual([], record["evidence"])
            self.assertEqual([], record["conditions"])
            self.assertTrue(record["manual_review_required"])
            self.assertIn("investigation_error:TypeError", record["limitations"])
            self.assertEqual(record["attempted_at"], record["exception_partial_record"]["attempted_at"])
            self.assertLess(record["attempted_at"], record["completed_at"])
            self.assertEqual(record["fetches"], record["exception_partial_record"]["fetches"])
            self.assertEqual("attempts/1301/prior.json", record["previous_attempts"][0])
            self.assertEqual(old, json.loads((output / record["previous_attempts"][1]).read_text()))
            self.assertEqual(prior_bytes, prior.read_bytes())
            snapshots = [json.loads((output / f["snapshot"]).read_text()) for f in record["fetches"]]
            self.assertTrue(all(s["http_get_attempted"] and s["http_status"] == 200 for s in snapshots))
            self.assertEqual(3, len(list((output / "evidence/1301").rglob("*.json"))))
            self.assertFalse(any(f["url"] == list(pages)[3] for f in record["fetches"]))
            # A strong saved form remains available for manual review; the failed
            # investigation cannot publish it as a completed confirmed result.
            self.assertEqual("form_fields_verified", research.analyze_page(snapshots[2])["level"])
            self.assertTrue(all(response.__exit__.call_count == 1 for response in responses))

    def test_exception_before_first_capture_keeps_complete_unconfirmed_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), ["1301"])
            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), \
                    patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 200, "新規上場")), \
                    patch.object(research.Fetcher, "capture", side_effect=TypeError("offline capture failure")), \
                    redirect_stdout(stdout):
                self.assertEqual(0, research.main())
            record = json.loads((output / "records/1301.json").read_text())
            self.assertEqual("unconfirmed", record["investigation_status"])
            self.assertEqual("none", record["verification_level"])
            self.assertEqual("not_stated", record["individual_access"])
            self.assertEqual("unconfirmed", record["outreach_suitability"])
            self.assertEqual("https://issuer1301.invalid/", record["official_url"])
            self.assertIsNone(record["contact_url"])
            for field in ("channels", "public_ir_emails", "evidence", "fetches", "conditions", "identity_matches"):
                self.assertEqual([], record[field])
            self.assertEqual(0, record["successful_official_page_count"])
            self.assertEqual(0, record["http_get_attempt_count"])
            self.assertEqual("unverified", record["identity_status"])
            self.assertIsNotNone(datetime.fromisoformat(record["attempted_at"]).tzinfo)
            self.assertIsNotNone(datetime.fromisoformat(record["completed_at"]).tzinfo)
            self.assertEqual(json.loads(originals["1301"]), json.loads((output / record["previous_attempts"][0]).read_text()))

    def test_mid_run_circuit_keeps_unstarted_records_and_resumes_them(self):
        codes = ["1301", "1302", "1303", "1304", "1305", "1306"]
        failure = "Invalid argument|remote address:envoy://cloudflare_https_tunnel/"
        attempted = []

        def outage_response(url, **kwargs):
            attempted.append(url)
            if "www.jpx.co.jp" in url:
                return self.response(url, 200, "新規上場")
            if "issuer1301.invalid" not in url:
                return self.response(url, 503, failure)
            if url.endswith("robots.txt"):
                return self.response(url, 404, "")
            return self.response(url, 200, '<title>IRお問い合わせ</title>Company1301 IRお問い合わせ E-mail ir@issuer.invalid')

        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), codes, missing=("1306",))
            old_snapshot = output / "evidence" / "old.json"
            research.write_json(old_snapshot, {"text": "immutable previous evidence"})
            old_bytes = old_snapshot.read_bytes()
            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), patch.object(research.requests, "get", side_effect=outage_response), redirect_stdout(stdout):
                self.assertEqual(2, research.main())
            run = json.loads(stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual("environment_stopped", run["status"])
            self.assertEqual(4, run["completed_in_this_run"])
            self.assertEqual(4, run["companies_with_actual_get_count"])
            # Robots failures do not dispatch a second GET for company content.
            self.assertEqual(5, run["company_http_get_attempt_count"])
            self.assertEqual(6, run["http_get_attempt_count"])
            self.assertEqual(6, len(attempted))
            self.assertEqual(["1305", "1306"], run["not_saved_security_codes"])
            self.assertEqual(originals["1305"], (output / "records" / "1305.json").read_bytes())
            self.assertFalse((output / "records" / "1306.json").exists())
            self.assertFalse((output / "attempts" / "1305").exists())
            for code in codes[:4]:
                archive = next((output / "attempts" / code).glob("*.json"))
                self.assertEqual(json.loads(originals[code]), json.loads(archive.read_text()))
            self.assertFalse(any("issuer1305" in url or "issuer1306" in url for url in attempted))
            preserved = (output / "records" / "1301.json").read_bytes()
            captured = {path: path.read_bytes() for path in (output / "evidence").rglob("*.json")}
            attempted.clear()

            def restored_response(url, **kwargs):
                attempted.append(url)
                if "www.jpx.co.jp" in url:
                    return self.response(url, 200, "新規上場")
                if url.endswith("robots.txt"):
                    return self.response(url, 404, "")
                code = research.urlsplit(url).hostname.removeprefix("issuer").removesuffix(".invalid")
                return self.response(url, 200, f'<title>IRお問い合わせ</title>Company{code} IRお問い合わせ E-mail ir@issuer.invalid')

            resumed_stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), patch.object(research.requests, "get", side_effect=restored_response), redirect_stdout(resumed_stdout):
                self.assertEqual(0, research.main())
            resumed = json.loads(resumed_stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual("completed", resumed["status"])
            self.assertEqual(5, resumed["selected_company_count"])
            self.assertEqual(5, resumed["completed_in_this_run"])
            self.assertEqual([], resumed["not_saved_security_codes"])
            self.assertEqual(11, resumed["http_get_attempt_count"])
            self.assertFalse(any("issuer1301" in url for url in attempted))
            self.assertEqual(preserved, (output / "records" / "1301.json").read_bytes())
            for path, content in captured.items():
                self.assertEqual(content, path.read_bytes())
            self.assertEqual(old_bytes, old_snapshot.read_bytes())
            self.assertEqual(2, len([x for x in (output / "collection-runs").glob("*.json") if not x.name.endswith("-progress.json")]))

    def test_global_dispatch_rate_includes_preflight_robots_and_redirects(self):
        fetcher = research.Fetcher(delay=1, global_rps=2)
        dispatches = []

        def response(url, **kwargs):
            dispatches.append((url, self.clock.monotonic()))
            if url.endswith("robots.txt"):
                return self.response(url, 404, "")
            if url == "https://issuer.invalid/":
                value = self.response(url, 302, "")
                value.headers["Location"] = "https://target.invalid/contact"
                return value
            return self.response(url, 200, "新規上場 IR contact")

        with patch.object(research.requests, "get", side_effect=response):
            fetcher.raw_get("https://jpx.invalid/preflight")
            captured = fetcher.capture("https://issuer.invalid/")
        self.assertEqual(5, len(dispatches))
        gaps = [b[1] - a[1] for a, b in zip(dispatches, dispatches[1:])]
        self.assertTrue(all(gap >= 0.5 for gap in gaps), dispatches)
        for hostname in ("issuer.invalid", "target.invalid"):
            ticks = [tick for url, tick in dispatches if research.urlsplit(url).hostname == hostname]
            self.assertGreaterEqual(ticks[1] - ticks[0], 1)
        self.assertIn("http_get_started_at", captured["redirects"][0])
        self.assertIsNotNone(captured["http_get_completed_at"])
        self.assertEqual(5, fetcher.http_get_attempt_count)

    def test_timing_and_safe_headers_cover_429_without_retrying_origin(self):
        fetcher = research.Fetcher(delay=1, global_rps=1)

        def response(url, **kwargs):
            self.clock.advance(0.2)  # time until response headers
            value = self.response(url, 429, "Too Many Requests")
            value.headers.update({"Retry-After": "5", "RateLimit-Remaining": "0", "X-RateLimit-Limit": "20",
                                  "Server": "envoy", "Date": "Sun, 11 Oct 2026 00:00:00 GMT",
                                  "Via": "proxy", "X-Request-ID": "public-trace", "Set-Cookie": "secret",
                                  "Authorization": "secret", "Proxy-Authorization": "secret"})

            def chunks(size):
                self.clock.advance(0.3)  # streamed body
                yield b"Too Many Requests"

            value.iter_content.side_effect = chunks
            return value

        with patch.object(research.requests, "get", side_effect=response) as request:
            first = fetcher.raw_get("https://issuer.invalid/")
            second = fetcher.raw_get("https://issuer.invalid/ir")
        self.assertEqual(1, request.call_count)
        self.assertEqual(5, first["retry_after_seconds"])
        self.assertEqual("http_429", first["failure_signature"])
        self.assertEqual(1, fetcher.stats()["http_429_count"])
        self.assertAlmostEqual(0.5, first["http_get_elapsed_seconds"])
        self.assertLess(first["http_get_started_at"], first["http_response_received_at"])
        self.assertLess(first["http_response_received_at"], first["http_get_completed_at"])
        self.assertEqual("public-trace", first["response_headers"]["x-request-id"])
        self.assertNotIn("set-cookie", first["response_headers"])
        self.assertNotIn("authorization", first["response_headers"])
        self.assertNotIn("proxy-authorization", first["response_headers"])
        self.assertEqual("host_access_denied_stopped", second["error"])
        self.assertFalse(second["http_get_attempted"])
        self.assertIsNone(second["http_get_started_at"])

    def test_concurrent_origins_share_one_smooth_dispatch_gate(self):
        fetcher = research.Fetcher(delay=1, global_rps=2)
        barrier = threading.Barrier(8)
        dispatched = []

        def response(url, **kwargs):
            dispatched.append(self.clock.monotonic())
            return self.response(url, 200, "public page")

        def fetch(number):
            barrier.wait(timeout=2)
            return fetcher.raw_get(f"https://host{number}.invalid/")

        with patch.object(research.requests, "get", side_effect=response):
            with research.concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(fetch, range(8)))
        self.assertEqual(8, len(dispatched))
        self.assertTrue(all(b - a >= 0.5 for a, b in zip(dispatched, dispatched[1:])), dispatched)
        self.assertEqual(8, fetcher.http_get_attempt_count)
        self.assertTrue(all(result["http_get_completed_at"] for result in results))

    def test_four_origins_can_wait_for_headers_with_spaced_get_starts(self):
        fetcher = research.Fetcher(delay=1, global_rps=3)
        release_headers, all_started = threading.Event(), threading.Event()
        guard = threading.Lock()
        dispatches = []
        active = maximum_active = 0

        def slow_headers(url, **kwargs):
            nonlocal active, maximum_active
            with guard:
                dispatches.append((url, self.clock.monotonic()))
                active += 1
                maximum_active = max(maximum_active, active)
                if active == 4:
                    all_started.set()
            release_headers.wait(timeout=2)
            with guard:
                active -= 1
            return self.response(url, 200, "public page")

        with patch.object(research.requests, "get", side_effect=slow_headers):
            with research.concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(fetcher.raw_get, f"https://host{i}.invalid/") for i in range(4)]
                overlapping = all_started.wait(timeout=0.5)
                release_headers.set()
                results = [future.result(timeout=2) for future in futures]
        self.assertTrue(overlapping, "A slow response header must not retain the global dispatch lock")
        self.assertEqual(4, maximum_active)
        self.assertEqual(4, fetcher.http_get_attempt_count)
        gaps = [b[1] - a[1] for a, b in zip(dispatches, dispatches[1:])]
        self.assertTrue(all(gap >= 1 / 3 - 1e-12 for gap in gaps), dispatches)
        self.assertTrue(all(result["http_get_completed_at"] for result in results))
        recorded = sorted(datetime.fromisoformat(result["http_get_started_at"]) for result in results)
        self.assertTrue(all((b - a).total_seconds() >= 0.333333 for a, b in zip(recorded, recorded[1:])))

    def test_slow_origin_serializes_its_own_gets_while_other_origin_proceeds(self):
        fetcher = research.Fetcher(delay=1, global_rps=3)
        first_started, unrelated_started, second_started = (threading.Event() for _ in range(3))
        release_first = threading.Event()
        starts = {}

        def response(url, **kwargs):
            starts[url] = self.clock.monotonic()
            if url == "https://slow.invalid/first":
                first_started.set()
                release_first.wait(timeout=2)
            elif url == "https://slow.invalid/second":
                second_started.set()
            else:
                unrelated_started.set()
            return self.response(url, 200, "public page")

        with patch.object(research.requests, "get", side_effect=response):
            with research.concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                first = pool.submit(fetcher.raw_get, "https://slow.invalid/first")
                self.assertTrue(first_started.wait(timeout=0.5))
                second = pool.submit(fetcher.raw_get, "https://slow.invalid/second")
                unrelated = pool.submit(fetcher.raw_get, "https://other.invalid/")
                independent_progress = unrelated_started.wait(timeout=0.5)
                same_origin_started_early = second_started.is_set()
                release_first.set()
                for future in (first, second, unrelated):
                    future.result(timeout=2)
        self.assertTrue(independent_progress, "Another origin must proceed while the first waits for headers")
        self.assertFalse(same_origin_started_early)
        self.assertGreaterEqual(starts["https://slow.invalid/second"] - starts["https://slow.invalid/first"], 1)

    def test_rate_reduction_during_dispatch_wait_rechecks_the_new_interval(self):
        fetcher = research.Fetcher(delay=1, global_rps=2)
        waits = []

        def wait(seconds):
            waits.append(seconds)
            if len(waits) == 1:
                self.clock.advance(seconds / 2)
                fetcher._observe_response({"http_status": 503,
                                           "text": "Invalid argument|remote address:envoy://cloudflare_https_tunnel/"},
                                          "https://failed.invalid")
            else:
                self.clock.advance(seconds)
            return False

        with patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 200, "public")) as request:
            fetcher.raw_get("https://one.invalid/")
            with patch.object(fetcher, "wait_for_delay", side_effect=wait), redirect_stdout(io.StringIO()):
                second = fetcher.raw_get("https://two.invalid/")
        self.assertEqual([0.5, 1.0], waits)
        self.assertEqual(1, fetcher.global_rps)
        self.assertEqual(1, second["global_rps_at_dispatch"])
        self.assertEqual(self.clock.iso(), second["http_get_started_at"])
        self.assertEqual(1.25, self.clock.monotonic())
        self.assertEqual(2, request.call_count)

    def test_common_503_halves_rate_and_stops_at_three_origins(self):
        fetcher = research.Fetcher(delay=0, global_rps=2)
        text = "Invalid argument|remote address:envoy://cloudflare_https_tunnel/"
        with patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 503, text)), redirect_stdout(io.StringIO()) as stdout:
            rates = []
            for host in ("one", "two", "three"):
                fetcher.raw_get(f"https://{host}.invalid/")
                rates.append(fetcher.global_rps)
            stopped = fetcher.raw_get("https://four.invalid/")
        self.assertEqual([1, 0.5, 0.25], rates)
        self.assertEqual(3, fetcher.stats()["common_transport_503_count"])
        self.assertEqual(3, fetcher.http_get_attempt_count)
        self.assertEqual("environment_circuit_breaker_open", stopped["error"])
        self.assertEqual(3, len(stdout.getvalue().splitlines()))

    def test_site_tls_503_does_not_reduce_global_rate(self):
        fetcher = research.Fetcher(delay=0, global_rps=2)
        bodies = ["TLS_error: CERTIFICATE_VERIFY_FAILED", "TLS_error: WRONG_VERSION_NUMBER", "reset reason: connection termination"]
        with patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 503, bodies.pop(0))):
            results = [fetcher.raw_get(f"https://host{i}.invalid/") for i in range(3)]
        self.assertEqual(2, fetcher.global_rps)
        self.assertFalse(fetcher.environment_failed.is_set())
        self.assertEqual(3, fetcher.stats()["site_specific_503_count"])
        self.assertEqual("site_connection_termination_503", results[-1]["failure_signature"])

    def test_generic_503_backoff_is_per_origin_and_has_a_floor(self):
        fetcher = research.Fetcher(delay=0, global_rps=1)
        with patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 503, "Service unavailable")), redirect_stdout(io.StringIO()):
            fetcher.raw_get("https://one.invalid/")
            self.assertEqual(0.8, fetcher.global_rps)
            fetcher.raw_get("https://one.invalid/ir")
            self.assertEqual(0.8, fetcher.global_rps)
            for host in range(20):
                fetcher.raw_get(f"https://other{host}.invalid/")
        self.assertEqual(0.25, fetcher.global_rps)
        self.assertFalse(fetcher.environment_failed.is_set())
        self.assertEqual(22, fetcher.http_get_attempt_count)

    def test_global_dispatch_wait_interrupts_before_actual_get(self):
        fetcher = research.Fetcher(delay=0, global_rps=1)
        with patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 200, "public")) as request:
            fetcher.raw_get("https://one.invalid/")

            def stop(seconds):
                fetcher.environment_failed.set()
                return True

            with patch.object(fetcher, "wait_for_delay", side_effect=stop):
                interrupted = fetcher.raw_get("https://two.invalid/")
        self.assertEqual(1, request.call_count)
        self.assertFalse(interrupted["http_get_attempted"])
        self.assertIsNone(interrupted["http_get_started_at"])
        self.assertEqual("environment_circuit_breaker_open", interrupted["error"])

    def test_retry_after_http_date_and_request_exception_are_observable(self):
        fetcher = research.Fetcher(delay=0)
        value = self.response("https://one.invalid/", 429, "Too many requests")
        value.headers["Retry-After"] = "Sun, 11 Oct 2026 00:00:10 GMT"
        with patch.object(research.requests, "get", return_value=value):
            limited = fetcher.raw_get("https://one.invalid/")
        self.assertEqual(10, limited["retry_after_seconds"])
        with patch.object(research.requests, "get", side_effect=research.requests.exceptions.ProxyError("proxy details must not be logged")):
            failed = fetcher.raw_get("https://two.invalid/")
        self.assertEqual("request_exception:ProxyError", failed["failure_signature"])
        self.assertTrue(failed["http_get_attempted"])
        self.assertIsNotNone(failed["http_get_completed_at"])
        self.assertNotIn("proxy details", json.dumps(failed))

    def test_global_rps_cli_rejects_nonfinite_zero_and_above_limit(self):
        for value in ("nan", "inf", "0", "-1", "4.1"):
            with self.subTest(value=value), patch.object(research.sys, "argv", [str(SCRIPT), "--universe", "unused.csv", "--seeds", "unused.json", "--output", "unused", "--global-rps", value]), redirect_stdout(io.StringIO()), patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    research.main()
                self.assertEqual(2, raised.exception.code)

    def test_followup_keeps_prior_contact_and_separates_latest_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), ["1301", "1302"])
            old_path = output / "records" / "1301.json"
            old = json.loads(old_path.read_text())
            old.update(investigation_status="confirmed", verification_level="ir_email_verified", contact_url="https://issuer1301.invalid/ir/contact",
                       attempted_at="2026-10-10T00:00:00+00:00", completed_at="2026-10-10T00:00:01+00:00",
                       public_ir_emails=["ir@issuer.invalid"], channels=["email"], http_get_attempt_count=99,
                       evidence=[{"snapshot": "evidence/prior.json", "quote": "IR E-mail ir@issuer.invalid"}], manual_review_required=False)
            old.pop("unconfirmed_reason")
            research.write_json(old_path, old)
            research.write_json(output / "evidence" / "prior.json", {"text": "IR E-mail ir@issuer.invalid"})
            prior_bytes = (output / "evidence" / "prior.json").read_bytes()
            argv.remove("--resume-network-errors")
            argv.extend(["--only-codes", "1301"])
            stdout = io.StringIO()

            def failed_response(url, **kwargs):
                return self.response(url, 200, "新規上場") if "jpx.co.jp" in url else self.response(url, 404, "missing")

            with patch.object(research.sys, "argv", argv), patch.object(research.requests, "get", side_effect=failed_response), redirect_stdout(stdout):
                self.assertEqual(0, research.main())
            kept = json.loads(old_path.read_text())
            self.assertEqual(old["contact_url"], kept["contact_url"])
            self.assertEqual(old["evidence"], kept["evidence"])
            self.assertEqual(old["completed_at"], kept["completed_at"])
            self.assertTrue(kept["retained_prior_contact"])
            self.assertTrue(kept["needs_contact_recheck"])
            self.assertEqual("unconfirmed", kept["latest_attempt"]["investigation_status"])
            self.assertEqual(2, kept["latest_attempt"]["http_get_attempt_count"])
            self.assertEqual(originals["1302"], (output / "records" / "1302.json").read_bytes())
            self.assertEqual(prior_bytes, (output / "evidence" / "prior.json").read_bytes())
            archived = json.loads((output / kept["previous_attempts"][-1]).read_text())
            self.assertEqual(old, archived)
            run = json.loads(stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual(2, run["company_http_get_attempt_count"])
            self.assertEqual(1, run["companies_with_actual_get_count"])
            self.assertEqual(["1301"], run["saved_security_codes"])

            def restored_response(url, **kwargs):
                if "jpx.co.jp" in url:
                    return self.response(url, 200, "新規上場")
                if url.endswith("robots.txt"):
                    return self.response(url, 404, "")
                return self.response(url, 200, '<title>IRお問い合わせ</title>Company1301 IRお問い合わせ E-mail ir@issuer.invalid')

            with patch.object(research.sys, "argv", argv), patch.object(research.requests, "get", side_effect=restored_response), redirect_stdout(io.StringIO()):
                self.assertEqual(0, research.main())
            fresh = json.loads(old_path.read_text())
            self.assertEqual("confirmed", fresh["investigation_status"])
            self.assertNotIn("retained_prior_contact", fresh)
            self.assertTrue(fresh["manual_review_required"])
            self.assertEqual(2, len(fresh["previous_attempts"]))
            self.assertEqual(prior_bytes, (output / "evidence" / "prior.json").read_bytes())

    def test_resume_unconfirmed_obeys_seed_filter_and_small_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), ["1301", "1302", "1303"])
            seed_path = Path(argv[argv.index("--seeds") + 1])
            seed_path.write_text(json.dumps([{"security_code": "1302", "official_url": "https://issuer1302.invalid/"}]))
            argv.remove("--resume-network-errors")
            argv.extend(["--resume-unconfirmed", "--only-seeded", "--limit", "1"])

            def response(url, **kwargs):
                if "jpx.co.jp" in url:
                    return self.response(url, 200, "新規上場")
                if url.endswith("robots.txt"):
                    return self.response(url, 404, "")
                return self.response(url, 200, '<title>IRお問い合わせ</title>Company1302 IRお問い合わせ E-mail ir@issuer.invalid')

            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), patch.object(research.requests, "get", side_effect=response), redirect_stdout(stdout):
                self.assertEqual(0, research.main())
            run = json.loads(stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual(1, run["selected_company_count"])
            self.assertEqual(["1302"], run["saved_security_codes"])
            self.assertEqual(1, run["workers"])
            self.assertEqual(1.0, run["configured_global_rps"])
            self.assertEqual(1.0, run["final_global_rps"])
            self.assertTrue(run["preflight_passed"])
            self.assertEqual(200, run["preflight_http_status"])
            self.assertEqual(run, json.loads((output / run["progress_path"]).read_text()))
            self.assertEqual(run, json.loads((output / run["run_path"]).read_text()))
            for code in ("1301", "1303"):
                self.assertEqual(originals[code], (output / "records" / f"{code}.json").read_bytes())

    def test_progress_preserves_existing_fifty_company_compile_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            codes = [str(code) for code in range(1301, 1351)]
            output, argv, originals = self.survey_fixture(Path(temporary), codes)

            def response(url, **kwargs):
                if "jpx.co.jp" in url:
                    return self.response(url, 200, "新規上場")
                if url.endswith("robots.txt"):
                    return self.response(url, 404, "")
                code = research.urlsplit(url).hostname.removeprefix("issuer").removesuffix(".invalid")
                return self.response(url, 200, f'<title>IRお問い合わせ</title>Company{code} IRお問い合わせ E-mail ir@issuer.invalid')

            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), patch.object(research.requests, "get", side_effect=response), \
                    patch.object(research, "compile_directory", wraps=research.compile_directory) as compile_directory, redirect_stdout(stdout):
                self.assertEqual(0, research.main())
            self.assertEqual(2, compile_directory.call_count)  # after 50, and final
            messages = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(50, messages[0]["completed_in_this_run"])
            self.assertEqual(101, messages[-1]["collection_run"]["http_get_attempt_count"])
            run = messages[-1]["collection_run"]
            self.assertEqual("completed", json.loads((output / run["progress_path"]).read_text())["status"])

    def test_running_worker_without_get_preserves_original_on_circuit_stop(self):
        fetcher = research.Fetcher(delay=0)
        zero_get_worker_started = threading.Event()
        failure = "Invalid argument|remote address:envoy://cloudflare_https_tunnel/"

        def public_response(url, **kwargs):
            return self.response(url, 200 if "jpx.co.jp" in url else 503,
                                 "新規上場" if "jpx.co.jp" in url else failure)

        def controlled_investigation(company, seed, output, current_fetcher, max_pages, record=None):
            if company["security_code"] == "1301":
                self.assertTrue(zero_get_worker_started.wait(2))
                for host in ("one", "two", "three"):
                    current_fetcher.raw_get(f"https://{host}.invalid/")
            else:
                zero_get_worker_started.set()
                self.assertTrue(current_fetcher.environment_failed.wait(2))
            return {**company, "investigation_status": "unconfirmed", "verification_level": "none",
                    "outreach_suitability": "unconfirmed", "unconfirmed_reason": "environment_transport_failure",
                    "evidence": [], "fetches": []}

        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), ["1301", "1302", "1303"])
            argv[argv.index("--workers") + 1] = "2"
            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), patch.object(research, "Fetcher", return_value=fetcher), \
                    patch.object(research.requests, "get", side_effect=public_response), \
                    patch.object(research, "investigation", side_effect=controlled_investigation), redirect_stdout(stdout):
                self.assertEqual(2, research.main())
            run = json.loads(stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual(1, run["completed_in_this_run"])
            self.assertEqual(1, run["companies_with_actual_get_count"])
            self.assertEqual(3, run["company_http_get_attempt_count"])
            self.assertEqual(["1302", "1303"], run["not_saved_security_codes"])
            for code in ("1302", "1303"):
                self.assertEqual(originals[code], (output / "records" / f"{code}.json").read_bytes())
                self.assertFalse((output / "attempts" / code).exists())

    def test_host_lock_waiter_does_not_get_after_circuit_opens(self):
        fetcher = research.Fetcher(delay=0)
        url = "https://issuer.invalid/"
        lock = threading.Lock()
        entered = threading.Event()

        class ObservedLock:
            def __enter__(self):
                entered.set()  # raw_get has passed the first circuit check.
                lock.acquire()

            def __exit__(self, *args):
                lock.release()

        fetcher.locks["https://issuer.invalid"] = ObservedLock()
        result = []
        lock.acquire()

        def worker():
            result.append(fetcher.raw_get(url))

        thread = threading.Thread(target=worker, daemon=True)
        with patch.object(research.requests, "get") as request:
            thread.start()
            self.assertTrue(entered.wait(2))
            fetcher.environment_failed.set()
            lock.release()
            thread.join(2)
            self.assertFalse(thread.is_alive())
            request.assert_not_called()
        self.assertEqual("environment_circuit_breaker_open", result[0]["error"])
        self.assertEqual(0, fetcher.http_get_attempt_count)

    def test_queued_future_is_cancelled_without_record_or_archive_change(self):
        fetcher = research.Fetcher(delay=0)
        tasks = {}

        class QueuedPool:
            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def submit(self, function, company):
                future = research.concurrent.futures.Future()
                tasks[future] = (function, company)
                return future

        # Deterministically open the circuit while a second company is queued.
        def finish_first(futures, **kwargs):
            future = next(iter(futures))
            function, company = tasks[future]
            future.set_running_or_notify_cancel()
            future.set_result(function(company))
            return {future}, set(futures) - {future}

        def stop_during_investigation(company, seed, output, current_fetcher, max_pages, record=None):
            current_fetcher.raw_get("https://one.invalid/")
            current_fetcher.environment_failed.set()
            return {**company, "investigation_status": "unconfirmed", "verification_level": "none",
                    "outreach_suitability": "unconfirmed", "unconfirmed_reason": "environment_transport_failure",
                    "fetches": [], "evidence": []}

        with tempfile.TemporaryDirectory() as temporary:
            output, argv, originals = self.survey_fixture(Path(temporary), ["1301", "1302", "1303"])
            argv[argv.index("--workers") + 1] = "2"
            stdout = io.StringIO()
            with patch.object(research.sys, "argv", argv), patch.object(research, "Fetcher", return_value=fetcher), \
                    patch.object(research.requests, "get", side_effect=lambda url, **kwargs: self.response(url, 200, "新規上場")), \
                    patch.object(research, "investigation", side_effect=stop_during_investigation), \
                    patch.object(research.concurrent.futures, "ThreadPoolExecutor", QueuedPool), \
                    patch.object(research.concurrent.futures, "wait", side_effect=finish_first), redirect_stdout(stdout):
                self.assertEqual(2, research.main())
            run = json.loads(stdout.getvalue().splitlines()[-1])["collection_run"]
            self.assertEqual(2, run["submitted_company_count"])
            self.assertEqual(1, run["cancelled_future_count"])
            self.assertEqual(1, run["completed_in_this_run"])
            self.assertEqual(["1302", "1303"], run["not_saved_security_codes"])
            self.assertTrue(next(f for f, (_, c) in tasks.items() if c["security_code"] == "1302").cancelled())
            for code in ("1302", "1303"):
                self.assertEqual(originals[code], (output / "records" / f"{code}.json").read_bytes())
                self.assertFalse((output / "attempts" / code).exists())

    def test_failed_preflight_keeps_existing_record_and_no_retry_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            universe, seeds, output = root / "input.csv", root / "seeds.json", root / "survey"
            universe.write_text("security_code,company_name,market,jpx_sector\n1301,Example,スタンダード（内国株式）,水産・農林業\n", encoding="utf-8")
            seeds.write_text(json.dumps([{"security_code": "1301", "official_url": "https://issuer.example/"}]))
            (output / "records").mkdir(parents=True)
            record = output / "records" / "1301.json"
            record.write_text(json.dumps({"security_code": "1301", "unconfirmed_reason": "environment_transport_failure", "preserved": "original attempt"}))
            original = record.read_bytes()
            argv = [str(SCRIPT), "--universe", str(universe), "--seeds", str(seeds), "--output", str(output), "--resume-network-errors", "--workers", "1"]
            failure = {"requested_url": "https://www.jpx.co.jp/listing/stocks/new/index.html", "http_status": 503, "text": "proxy outage", "submitted": False, "retrieved_at": research.now()}
            with patch.object(research.sys, "argv", argv), patch.object(research.Fetcher, "raw_get", return_value=failure) as request, redirect_stdout(io.StringIO()):
                self.assertEqual(2, research.main())
            self.assertEqual(original, record.read_bytes())
            self.assertFalse((output / "attempts").exists())
            self.assertEqual(1, request.call_count)

    def test_new_attempt_uses_new_snapshot_paths_and_preserves_original(self):
        class SavedPageFetcher:
            def capture(self, url):
                return {"requested_url": url, "url": url, "http_status": 200, "text": "Example investor relations enquiry ir@issuer.invalid", "title": "IR Contact", "headings": [], "links": [], "forms": [], "retrieved_at": research.now(), "submitted": False}

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            company = {"security_code": "1301", "company_name": "Example", "market": "スタンダード（内国株式）", "jpx_sector": "水産・農林業"}
            seed = {"official_url": "https://issuer.example/", "discovery_url": "https://listing.example/"}
            first = research.investigation(company, seed, root, SavedPageFetcher(), 1)
            path = root / first["fetches"][0]["snapshot"]
            original = path.read_bytes()
            second = research.investigation(company, seed, root, SavedPageFetcher(), 1)
            self.assertNotEqual(first["fetches"][0]["snapshot"], second["fetches"][0]["snapshot"])
            self.assertEqual(original, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
