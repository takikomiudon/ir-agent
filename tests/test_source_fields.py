"""Source field binding must not round JSON decimals or choose duplicate keys."""
from copy import deepcopy
from decimal import Decimal
import unittest

from ir_agent.decision import _source_field, evaluate_decision
from test_decision import request


class SourceFieldTests(unittest.TestCase):
    def value(self, raw):
        value = request()
        value['sources'][1]['content'] = raw
        value['quote'].update(price_path=['content', 'price'], observed_at_path=['content', 'observed_at'])
        return value

    def test_decimal_tokens_in_saved_json_retain_their_exact_value(self):
        literal = '1000.000000000000000000000001'
        value = self.value('{"price": ' + literal + ', "observed_at": "2026-10-09T09:55:00+09:00"}')
        value['quote']['price_jpy'] = literal
        before = deepcopy(value)
        self.assertEqual(_source_field(value['sources'][1], ['content', 'price']), Decimal(literal))
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'buy_review')
        self.assertEqual(value, before)

    def test_duplicate_keys_cannot_be_selected_as_authoritative_source_fields(self):
        for prices in ('"price": 900, "price": 1000', '"price": 1000, "price": 1000'):
            value = self.value('{' + prices + ', "observed_at": "2026-10-09T09:55:00+09:00"}')
            with self.subTest(prices=prices), self.assertRaises(ValueError): evaluate_decision(value)

    def test_nonfinite_json_is_not_accepted_as_a_structured_source(self):
        for token in ('NaN', 'Infinity', '-Infinity'):
            value = self.value('{"price": 1000, "unrelated": ' + token + ', "observed_at": "2026-10-09T09:55:00+09:00"}')
            with self.subTest(token=token), self.assertRaises(ValueError): evaluate_decision(value)


if __name__ == '__main__': unittest.main()
