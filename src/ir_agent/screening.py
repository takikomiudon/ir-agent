"""Apply explicitly adopted screens to source-bound metrics, without ranking.

Adopted principle: Anthropic idea-generation, preserved at commit
574ed3624aebd0418c7e96cd101262f30210ab26: screens surface candidates, not
conclusions. This generic comparison engine is an independent local adaptation;
the upstream's illustrative numerical cutoffs are not operational defaults.
"""
from __future__ import annotations

from copy import deepcopy
from operator import eq, ge, gt, le, lt, ne

from .decision import _check_source_origins, _source_field
from .models import JST, available, day, integer, object_value, source_origins, text, timestamp, validate_source
from .valuation import _number


_OPERATORS = {"lt": lt, "le": le, "gt": gt, "ge": ge, "eq": eq, "ne": ne}
_BOUND_FIELDS = {"subject_id", "value", "unit", "definition", "period", "observed_at"}


def _period(value):
    value = object_value(value, "metric period")
    kind = value.get("kind")
    text(kind, "metric period.kind")
    if kind not in {"instant", "duration"}:
        raise ValueError("Metric period kind must be instant or duration")
    required = {"kind", "end"} if kind == "instant" else {"kind", "start", "end"}
    if set(value) != required:
        raise ValueError("Period must have exactly its kind and relevant date fields")
    end = day(value["end"], "period.end")
    if kind == "duration" and day(value["start"], "period.start") > end:
        raise ValueError("Metric period ends before it starts")
    return value


def _policy_issues(policy, synthetic, cutoff):
    if not isinstance(policy, dict) or not policy.get("rules"):
        return ["screening_rules_not_configured"]
    text(policy.get("id"), "policy.id")
    integer(policy.get("version"), "policy.version", minimum=1)
    text(policy.get("style"), "policy.style")
    if timestamp(policy.get("recorded_at"), "policy.recorded_at") > cutoff:
        return ["policy_not_available_at_as_of"]
    if set(policy) - {"id", "version", "recorded_at", "style", "supported_models", "rules"}:
        raise ValueError("Unknown screening policy field")
    models = policy.get("supported_models")
    if not isinstance(models, list) or not models:
        return ["supported_models_not_configured"]
    for model in models:
        text(model, "supported model")
    if len(set(models)) != len(models):
        raise ValueError("Duplicate supported model")
    if not isinstance(policy["rules"], list):
        raise ValueError("policy.rules must be a list")
    issues = []; seen = set()
    for rule in policy["rules"]:
        rule = object_value(rule, "screening rule")
        text(rule.get("id"), "rule.id"); text(rule.get("metric"), "rule.metric")
        if rule["id"] in seen:
            raise ValueError("Duplicate screening rule ID")
        seen.add(rule["id"])
        if set(rule) - {"id", "metric", "operator", "comparison", "source", "max_age_seconds"}:
            raise ValueError("Unknown screening rule field")
        text(rule.get("operator"), "rule.operator")
        if rule["operator"] not in _OPERATORS:
            raise ValueError("Unsupported screening comparison operator")
        if rule.get("max_age_seconds") is None:
            issues.append(rule["id"] + ":freshness_limit_not_configured")
        else:
            integer(rule["max_age_seconds"], "rule.max_age_seconds", minimum=1)
        source = rule.get("source")
        if isinstance(source, dict):
            text(source.get("kind"), "rule.source.kind")
        if not isinstance(source, dict) or source.get("kind") not in {"user", "external_policy", "synthetic_example"}:
            issues.append(rule["id"] + ":rule_source_missing")
        else:
            if set(source) - {"kind", "reference", "rationale"}:
                raise ValueError("Unknown screening rule source field")
            for field in ("reference", "rationale"):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    issues.append(rule["id"] + ":rule_source_" + field + "_missing")
            if source["kind"] == "synthetic_example" and not synthetic:
                issues.append(rule["id"] + ":synthetic_policy_requires_synthetic_context")
        comparison = rule.get("comparison")
        if isinstance(comparison, dict):
            text(comparison.get("kind"), "comparison.kind")
        if not isinstance(comparison, dict) or comparison.get("kind") not in {"value", "benchmark"}:
            issues.append(rule["id"] + ":comparison_not_configured")
            continue
        if comparison["kind"] == "benchmark":
            if set(comparison) != {"kind", "metric"}:
                raise ValueError("Benchmark comparison requires exactly kind and metric")
            text(comparison["metric"], "comparison.metric")
        else:
            required = {"kind", "value", "unit", "definition", "period"}
            if not required <= set(comparison) or comparison.get("value") is None:
                issues.append(rule["id"] + ":threshold_not_configured")
                continue
            if set(comparison) != required:
                raise ValueError("Unknown threshold comparison field")
            _number(comparison["value"], "threshold")
            text(comparison["unit"], "threshold unit"); text(comparison["definition"], "threshold definition")
            _period(comparison["period"])
    return issues


def _metric(name, metrics, sources, cutoff, age_limit, synthetic, company_id=None):
    value = metrics.get(name)
    if not isinstance(value, dict):
        return None, "metric_missing"
    if not (_BOUND_FIELDS | {"source_id", "bindings"}) <= set(value):
        return None, "metric_binding_incomplete"
    if set(value) != _BOUND_FIELDS | {"source_id", "bindings"}:
        raise ValueError("Unknown bound metric field")
    for field in ("subject_id", "source_id", "unit", "definition"):
        text(value[field], "metric." + field)
    if company_id is not None and value["subject_id"] != company_id:
        return None, "metric_belongs_to_another_company"
    numeric = _number(value["value"], "metric value")
    period = _period(value["period"])
    observed = timestamp(value["observed_at"], "metric.observed_at")
    source = sources.get(value["source_id"])
    if source is None:
        return None, "metric_source_missing"
    if source["company_id"] != value["subject_id"]:
        return None, "metric_source_belongs_to_another_subject"
    if source["metadata"].get("synthetic") is True and not synthetic:
        return None, "synthetic_source_requires_synthetic_context"
    if not available(source, cutoff):
        return None, "metric_source_not_available"
    lineage = _check_source_origins([source["id"]], sources, value["subject_id"], cutoff)
    if lineage:
        return None, lineage
    if not synthetic:
        pending, visited = [source["id"]], set()
        # The generic lineage guard above has already rejected missing/cyclic
        # links. A derived live-looking wrapper cannot launder a test fixture.
        while pending:
            origin_id = pending.pop()
            if origin_id in visited:
                continue
            visited.add(origin_id)
            origin = sources[origin_id]
            if origin["metadata"].get("synthetic") is True:
                return None, "synthetic_source_requires_synthetic_context"
            pending.extend(source_origins(origin))
    bindings = object_value(value["bindings"], "metric.bindings")
    if set(bindings) != _BOUND_FIELDS:
        return None, "metric_binding_incomplete"
    for field in _BOUND_FIELDS:
        saved = _source_field(source, bindings[field])
        if field == "value":
            same = _number(saved, "saved metric value") == numeric
        elif field == "observed_at":
            same = timestamp(saved, "saved metric observation") == observed
        else:
            same = saved == value[field]
        if not same:
            raise ValueError(f"Metric {name}.{field} differs from its saved source field")
    if observed > cutoff or observed > timestamp(source["retrieved_at"]):
        return None, "metric_observation_not_available"
    if day(period["end"]) > observed.astimezone(JST).date():
        return None, "metric_period_extends_beyond_observation"
    elapsed = cutoff - observed
    age_microseconds = (elapsed.days * 86400 + elapsed.seconds) * 1000000 + elapsed.microseconds
    if age_microseconds > age_limit * 1000000:
        return None, "metric_stale_under_policy"
    return value, None


def evaluate_screening(request: dict) -> dict:
    """Return candidate_for_research only after all explicit, sourced rules pass.

    No DB write, investment decision, IR availability inference, financial metric
    estimation, automatic unit conversion, or sector exclusion is performed.
    """
    request = deepcopy(object_value(request, "screening request"))
    if set(request) - {"company", "as_of", "metrics", "sources", "policy", "synthetic"}:
        raise ValueError("Unknown screening request field")
    company = object_value(request.get("company"), "company")
    text(company.get("id"), "company.id"); text(company.get("name"), "company.name")
    cutoff = timestamp(request.get("as_of"), "screening.as_of")
    synthetic = request.get("synthetic", False)
    if type(synthetic) is not bool:
        raise ValueError("synthetic must be boolean")
    policy = request.get("policy")
    result = {"company_id": company["id"], "as_of": cutoff.isoformat(), "synthetic": synthetic,
              "status": "needs_policy", "rule_results": [], "reason_codes": [],
              "principle_source": "Anthropic idea-generation, commit 574ed3624aebd0418c7e96cd101262f30210ab26",
              "interpretation": "Screening identifies research candidates; it neither activates a company nor recommends a trade. IR contact availability is a separate question."}
    issues = _policy_issues(policy, synthetic, cutoff)
    if issues:
        result["reason_codes"] = issues
        return result
    result["policy_snapshot"] = policy
    model = company.get("financial_model")
    if not isinstance(model, str) or not model.strip():
        result.update(status="needs_data", reason_codes=["financial_model_not_reviewed"])
        return result
    if model not in policy["supported_models"]:
        result.update(status="unsupported_model", reason_codes=["financial_model_not_supported_by_policy"])
        return result
    metrics = object_value(request.get("metrics", {}), "metrics")
    raw_sources = request.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ValueError("sources must be a list")
    sources = {}
    for raw in raw_sources:
        source = validate_source(raw)
        if source["id"] in sources:
            raise ValueError("Duplicate screening source ID")
        sources[source["id"]] = source
    for rule in policy["rules"]:
        row = {"rule_id": rule["id"], "status": "needs_data", "source": rule["source"], "reason_codes": []}
        left, issue = _metric(rule["metric"], metrics, sources, cutoff, rule["max_age_seconds"], synthetic, company["id"])
        comparison = rule["comparison"]
        right = comparison
        if issue:
            row["reason_codes"].append(issue)
        if comparison["kind"] == "benchmark":
            right, right_issue = _metric(comparison["metric"], metrics, sources, cutoff, rule["max_age_seconds"], synthetic)
            if right_issue:
                row["reason_codes"].append("benchmark:" + right_issue)
            elif left is not None and timestamp(left["observed_at"]) != timestamp(right["observed_at"]):
                row["reason_codes"].append("benchmark_observation_mismatch")
        if left is not None and right is not None:
            for field in ("unit", "definition", "period"):
                if left[field] != right[field]:
                    row["reason_codes"].append("comparison_" + field + "_mismatch")
        if not row["reason_codes"]:
            passed = _OPERATORS[rule["operator"]](_number(left["value"], "metric"), _number(right["value"], "comparison"))
            row.update(status="pass" if passed else "fail", metric=deepcopy(left), comparison=deepcopy(right))
        result["rule_results"].append(row)
    statuses = {row["status"] for row in result["rule_results"]}
    if "needs_data" in statuses:
        result.update(status="needs_data", reason_codes=["screening_data_incomplete_or_incomparable"])
    elif "fail" in statuses:
        result.update(status="does_not_match_policy", reason_codes=["one_or_more_adopted_rules_failed"])
    else:
        result.update(status="candidate_for_research", reason_codes=["all_adopted_rules_passed"])
    return result
