"""Single-forecast arithmetic tests; no empirical calibration claim."""

from copy import deepcopy
from decimal import Decimal, Inexact, InvalidOperation, ROUND_DOWN, Rounded, localcontext
from fractions import Fraction
import json
from pathlib import Path
import unittest

from ir_agent.probability_scoring import score_categorical_forecast


def request(probabilities=None, observed="b"):
    probabilities = {"a": ".2", "b": ".5", "c": ".3"} if probabilities is None else probabilities
    return {"categories": list(probabilities), "probabilities": probabilities,
            "observed_category": observed, "prediction_ref": "synthetic:prediction:1",
            "observation_ref": "synthetic:observation:1", "definition_ref": "synthetic:definitions:v1"}


class ProbabilityScoringTests(unittest.TestCase):
    def test_multiclass_full_squared_error_and_known_natural_log(self):
        result = score_categorical_forecast(request())
        # .2² + (.5-1)² + .3² = .38, independently using rational arithmetic.
        expected = sum((p-y)**2 for p, y in zip(
            [Fraction(1, 5), Fraction(1, 2), Fraction(3, 10)], [0, 1, 0]))
        self.assertEqual(Fraction(result["brier_loss"]["value"]), expected)
        self.assertEqual(result["log_loss"], {
            "status": "finite", "unit": "nats",
            "value": "0.69314718055994530941723212145817656807550013436025525412068000949339362196969472",
        })
        self.assertEqual(result["status"], "calculation_only")
        self.assertTrue(all(value is False for value in result["verification"].values()))

    def test_binary_full_vector_is_twice_scalar_brier(self):
        result = score_categorical_forecast(request({"a": ".25", "b": ".75"}))
        self.assertEqual(Fraction(result["brier_loss"]["value"]), 2 * (Fraction(3, 4)-1)**2)
        self.assertEqual(result["brier_loss"]["value"], "0.125")

    def test_zero_and_one_boundaries_distinguish_infinity_from_finite_zero(self):
        for predicted, observed, brier, log in [
            ({"a": "1", "b": "0"}, "b", "2", {"status": "positive_infinity", "value": None, "unit": "nats"}),
            ({"a": "1", "b": "0"}, "a", "0", {"status": "finite", "value": "0", "unit": "nats"}),
            ({"a": "1"}, "a", "0", {"status": "finite", "value": "0", "unit": "nats"}),
        ]:
            with self.subTest(observed=observed, predicted=predicted):
                result = score_categorical_forecast(request(predicted, observed))
                self.assertEqual(result["brier_loss"]["value"], brier)
                self.assertEqual(result["log_loss"], log)
                json.dumps(result, allow_nan=False)

    def test_label_and_mapping_order_do_not_change_scores_or_references(self):
        original = request()
        changed = deepcopy(original)
        changed["categories"] = ["c", "b", "a"]
        changed["probabilities"] = {"b": ".5", "c": ".3", "a": ".2"}
        a, b = score_categorical_forecast(original), score_categorical_forecast(changed)
        for key in ["brier_loss", "log_loss", "prediction_ref", "observation_ref", "definition_ref"]:
            self.assertEqual(a[key], b[key])
        self.assertEqual(b["categories"], changed["categories"])

    def test_very_small_positive_probability_is_not_clipped_or_rounded_to_zero(self):
        p = "1e-200"
        result = score_categorical_forecast(request({"a": p, "b": "0." + "9"*200}, "a"))
        expected = 2 * (1 - Fraction(1, 10**200))**2
        self.assertEqual(Fraction(result["brier_loss"]["value"]), expected)
        self.assertEqual(result["log_loss"]["status"], "finite")
        self.assertTrue(Decimal(result["log_loss"]["value"]) > 400)
        self.assertEqual(Fraction(result["probabilities"]["a"]), Fraction(1, 10**200))

    def test_exact_sum_and_types_reject_no_defaults_or_epsilon(self):
        bad = [None, {}, [], {"a": 0, "b": 0}, {"a": ".2", "b": ".7999999999999999999999999999999999999999999999999999999999999999999999999999999999999999"}]
        for value in bad:
            current = request()
            current["probabilities"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                score_categorical_forecast(current)
        current = request({"a": "0.1", "b": "0.2", "c": "0.7000000000000000000000000000000000000000000000000000000000000000000000000000000000000001"})
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            score_categorical_forecast(current)
        for number in [None, True, False, [], {}, "", " ", " 0.5", "0.5 ", "1_0", "NaN", "Infinity", "-Infinity", float("nan"), float("inf"), "-.1", "1.1"]:
            with self.subTest(number=number), self.assertRaises(ValueError):
                score_categorical_forecast(request({"a": number, "b": ".5"}))

    def test_request_keys_categories_observation_and_references_are_strict(self):
        for key in request():
            current = request()
            del current[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                score_categorical_forecast(current)
        invalid = [None, [], {**request(), "synthetic": True}]
        for key, values in {
            "categories": [[], {}, "a", ["a", "a"], ["a", None], ["a", " b"], ["a", " "]],
            "observed_category": [None, False, [], "", "d", "b "],
            "prediction_ref": [None, {}, "", " "],
            "observation_ref": [None, [], "", " "],
            "definition_ref": [None, False, "", " "],
        }.items():
            invalid.extend({**request(), key: value} for value in values)
        for current in invalid:
            with self.subTest(current=current), self.assertRaises(ValueError):
                score_categorical_forecast(current)

    def test_numeric_representations_and_caller_context_do_not_mutate_inputs_or_context(self):
        current = request({"a": Decimal(".2"), "b": .5, "c": ".3"})
        original = deepcopy(current)
        expected = score_categorical_forecast(current)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.Emax = 2
            context.Emin = -2
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            flags = dict(context.flags)
            result = score_categorical_forecast(current)
            self.assertEqual(context.prec, 2)
            self.assertEqual(context.rounding, ROUND_DOWN)
            self.assertEqual(dict(context.flags), flags)
        self.assertEqual(result, expected)
        self.assertEqual(current, original)
        score_categorical_forecast(request({"a": 0, "b": 1}))

    def test_preexisting_conversion_syntax_and_other_flags_are_preserved(self):
        with localcontext() as context:
            context.traps[InvalidOperation] = False
            # A real conversion error sets an InvalidOperation subcondition.
            # On C Decimal, SignalDict == plain dict can be false even without
            # any intervening operation. Compare matching representations.
            Decimal("not-a-number")
            Decimal(1) / Decimal(7)
            self.assertTrue(context.flags[InvalidOperation])
            self.assertTrue(context.flags[Inexact])
            self.assertTrue(context.flags[Rounded])
            public_flags = dict(context.flags)
            snapshot = context.copy()
            score_categorical_forecast(request())
            self.assertEqual(dict(context.flags), public_flags)
            self.assertEqual(context.flags, snapshot.flags)
            with self.assertRaises(ValueError):
                score_categorical_forecast(request({"a": "NaN", "b": "1"}))
            self.assertEqual(dict(context.flags), public_flags)
            self.assertEqual(context.flags, snapshot.flags)

    def test_resource_bounds_reject_instead_of_silently_rounding_or_expanding(self):
        for number in ["1e-1001", "0e-1001", "0." + "1"*257, "1e" + "9"*2048]:
            with self.subTest(number=number), self.assertRaises(ValueError):
                score_categorical_forecast(request({"a": number, "b": "1"}))
        current = request({f"category-{i}": "0" for i in range(1001)}, "category-0")
        with self.assertRaisesRegex(ValueError, "at most"):
            score_categorical_forecast(current)

    def test_synthetic_example_is_json_safe_and_has_no_probability_defaults(self):
        current = json.loads((Path(__file__).parents[1] / "examples/probability-scoring.json").read_text())
        self.assertTrue(all(current[key].startswith("synthetic:") for key in ["prediction_ref", "observation_ref", "definition_ref"]))
        result = score_categorical_forecast(current)
        self.assertEqual(result["brier_loss"]["value"], "0.38")
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
