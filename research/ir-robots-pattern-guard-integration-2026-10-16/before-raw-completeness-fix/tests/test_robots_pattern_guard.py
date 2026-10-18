"""Offline robots pattern regressions, including the saved J-STAGE policy."""
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.robotparser import RobotFileParser

from test_ir_contact_research import research

ROOT = Path(__file__).resolve().parents[1]


class RobotsPatternGuardTests(unittest.TestCase):
    def allowed(self, rules, path, agent=None):
        return research.robots_can_fetch(research.parse_robots(rules), agent or research.USER_AGENT,
                                         'https://issuer.invalid' + path)

    def test_saved_JSTAGE_PDF_is_denied_while_article_and_search_remain_allowed(self):
        folder = ROOT/'research/ir-japan-earnings-drift-method-discovery-2026-10-16'
        raw = (folder/'raw/970e4bff469232281c2c01fc7246a6d43090f0f3f697de6ceccb3447fa9fe5c1').read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), '970e4bff469232281c2c01fc7246a6d43090f0f3f697de6ceccb3447fa9fe5c1')
        capture = json.loads((folder/'capture.json').read_bytes())
        pdf = capture['GETs'][3]['html_visible_text']['links'][70]['url']
        self.assertIn('/_pdf/', pdf)
        parser = research.parse_robots(raw.decode('utf-8'))
        self.assertTrue(parser.can_fetch(research.USER_AGENT, pdf))  # Original stdlib bug.
        self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, pdf))
        self.assertFalse(research.robots_specific_allow_correction(parser, research.USER_AGENT, pdf))
        for i in (1, 2, 3):
            self.assertTrue(research.robots_can_fetch(parser, research.USER_AGENT, capture['GETs'][i]['url']))

    def test_multiple_wildcards_terminal_anchor_and_query_are_library_matched(self):
        rules = 'User-agent: *\nDisallow: /reports/*/draft*/*.pdf$'
        self.assertFalse(self.allowed(rules, '/reports/2026/draft-v1/report.pdf'))
        self.assertFalse(self.allowed(rules, '/reports//draft/report.pdf'))
        self.assertTrue(self.allowed(rules, '/reports/2026/final/report.pdf'))
        self.assertTrue(self.allowed(rules, '/reports/2026/draft/report.pdf?download=1'))
        query = 'User-agent: *\nDisallow: /search?key=a+b.[x]*$'
        self.assertFalse(self.allowed(query, '/search?key=a+b.[x]anything'))
        self.assertTrue(self.allowed(query, '/search?key=axbZxanything'))

    def test_percent_encoded_literal_star_and_dollar_are_not_rewritten_to_patterns(self):
        star = 'User-agent: *\nDisallow: /literal%2Aend'
        self.assertFalse(self.allowed(star, '/literal%2Aend'))
        self.assertTrue(self.allowed(star, '/literal-anything-end'))
        dollar = 'User-agent: *\nDisallow: /literal%24end'
        self.assertFalse(self.allowed(dollar, '/literal%24end'))
        self.assertTrue(self.allowed(dollar, '/literalend'))

    def test_legacy_first_matching_group_is_kept_instead_of_library_merging(self):
        rules = ('User-agent: ir-agent\nDisallow: /blocked*\n\n'
                 'User-agent: ir-agent-public-research\nAllow: /')
        self.assertFalse(self.allowed(rules, '/blocked/path'))
        self.assertTrue(self.allowed(rules, '/allowed'))
        self.assertTrue(self.allowed(rules, '/blocked/path', agent='unrelated/1'))
        rules = 'User-agent: named\nAllow: /\n\nUser-agent: *\nDisallow: /blocked*'
        self.assertTrue(self.allowed(rules, '/blocked/path', agent='named/1'))

    def test_pattern_allow_never_promotes_legacy_denial_or_saved_denial_recovery(self):
        rules = 'User-agent: *\nDisallow: /\nAllow: /public/*'
        parser = research.parse_robots(rules)
        target = 'https://issuer.invalid/public/notice'
        self.assertFalse(parser.can_fetch(research.USER_AGENT, target))
        self.assertFalse(research.robots_can_fetch(parser, research.USER_AGENT, target))
        self.assertFalse(research.robots_specific_allow_correction(parser, research.USER_AGENT, target))

    def test_unknown_raw_ambiguous_directive_or_reparsed_adapter_stops(self):
        target = 'https://issuer.invalid/public'
        vanilla = RobotFileParser()
        vanilla.parse(['User-agent: *', 'Disallow: /blocked*'])
        self.assertTrue(vanilla.can_fetch(research.USER_AGENT, target))
        self.assertFalse(research.robots_can_fetch(vanilla, research.USER_AGENT, target))
        ambiguous = research.parse_robots('User-agent: *\nDisallow: /x*\n\n'
            'User-agent: another\nDisallow: /x%2A')
        self.assertFalse(research.robots_can_fetch(ambiguous, research.USER_AGENT, target))
        adapter = research.parse_robots('User-agent: *\nDisallow: /x*')
        self.assertTrue(research.robots_can_fetch(adapter, research.USER_AGENT, target))
        adapter.parse(['User-agent: *', 'Disallow: /x%2A'])
        self.assertIsNone(adapter._ir_raw_robots_text)
        self.assertFalse(research.robots_can_fetch(adapter, research.USER_AGENT, target))

    def test_fresh_fetcher_stops_before_body_GET_for_pattern_denial(self):
        url = 'https://issuer.invalid/article/_pdf/report'
        robots_url = 'https://issuer.invalid/robots.txt'
        fetcher = research.Fetcher()
        def only_robots(target):
            self.assertEqual(target, robots_url, 'Body GET must remain unattempted')
            return {'url': target, 'http_status': 200, 'text': 'User-agent: *\nDisallow: /*_pdf'}
        with patch.object(fetcher, 'raw_get', side_effect=only_robots) as raw_get, \
                patch.object(research.requests, 'get', side_effect=AssertionError('No actual network')):
            result = fetcher.capture_one(url)
        raw_get.assert_called_once_with(robots_url)
        self.assertEqual(result['error'], 'robots_disallowed')
        self.assertFalse(result['http_get_attempted'])


if __name__ == '__main__':
    unittest.main()
