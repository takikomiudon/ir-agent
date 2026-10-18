"""Rebuild quotation metadata from saved bodies only; no network or scoring model."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

B = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    retrievals = json.loads((B / "retrievals.json").read_text())
    assert len(retrievals) <= 4
    assert len({r["url"] for r in retrievals}) == len(retrievals)
    for r in retrievals:
        assert r["attempt"] == 1 and r["method"] == "GET"
        assert sha(B / r["raw_file"]) == r["sha256"]
    sources = []
    specs = [
        ("gneiting-raftery-2007", "methodological_original", "2007-03", "usable"),
        ("fpp3-tscv", "author_book_chapter", None, "unavailable_body"),
        ("sklearn-cross-validation", "first_party_software_documentation", None, "usable"),
    ]
    for r, (sid, kind, date, availability) in zip(retrievals, specs):
        source = {"id": sid, **r, "source_kind": kind,
                  "publication_date": date, "availability": availability}
        if "text_file" in r:
            source["extracted_text_sha256"] = sha(B / r["text_file"])
        sources.append(source)
    quotes = []

    def quote(qid, source_index, text, location, page=None):
        s = sources[source_index]
        full = (B / s["text_file"]).read_text()
        target = full.split("\f")[page - 1] if page else full
        assert text in target, (qid, text)
        quotes.append({"id": qid, "source_id": s["id"], "text": text,
                       "location": location, "pdf_page": page,
                       "extracted_text_offset": full.index(text),
                       "raw_sha256": s["sha256"],
                       "extracted_text_sha256": s["extracted_text_sha256"]})

    quote("G1-realized-observation", 0,
          "Scoring rules assess the quality of probabilistic forecasts, by assigning a numerical score based on the predictive distribution and on the\n           event or value that materializes.",
          "Abstract; journal p359", 1)
    quote("G2-strict-properness", 0, "It is strictly proper if the maximum is unique.",
          "Abstract; journal p359", 1)
    quote("G3-brier", 0, "Example 1 (Quadratic or Brier score).", "Section 3.1, Example 1; journal p363", 5)
    quote("G4-brier-indicator", 0, "where δij = 1 if i = j and δij = 0 otherwise.",
          "Section 3.1, Example 1; journal p363", 5)
    quote("G5-log-formula", 0, "S(p, i) = log pi .", "Section 3.1, Example 3; journal p363", 5)
    quote("G6-log-unbounded", 0, "the logarithmic score has been criticized for its unboundedness,",
          "Section 3.1, Example 3; journal p363", 5)
    quote("G7-zero-event", 0, "S(0, 1) = −∞", "Section 3.2, boundary allowance; journal p363", 5)
    quote("G8-pre-observation", 0, "specified before any of the Xi ’s are observed; that is, there are",
          "Section 7.1, fully specified forecasting rule; journal p372", 14)
    quote("G9-low-probability", 0, "proper but involves a harsh penalty for low probability events",
          "Section 8.2; journal p374", 16)
    quote("C1-time-process", 2, "If one knows that the samples have been generated using a time-dependent process, it is safer to use a time-series aware cross-validation scheme .",
          "Section 3.1.2.1")
    quote("C2-group-structure", 2, "Similarly, if we know that the generative process has a group structure (samples collected from different subjects, experiments, measurement devices), it is safer to use group-wise cross-validation .",
          "Section 3.1.2.1")
    quote("C3-group-holdout", 2, "GroupKFold is a variation of K-fold which ensures that the same group is not represented in both testing and training sets.",
          "Section 3.1.2.4.1 Group k-fold")
    quote("C4-time-correlation", 2, "Time series data is characterized by the correlation between observations that are near in time ( autocorrelation ).",
          "Section 3.1.2.6")
    quote("C5-future", 2, "Therefore, it is very important to evaluate our model for time series data on the “future” observations least like those that are used to train the model.",
          "Section 3.1.2.6")
    quote("C6-fixed-intervals", 2, "This class can be used to cross-validate time series data samples that are observed at fixed time intervals.",
          "Section 3.1.2.6.1 Time Series Split")
    quote("C7-duration", 2, "Indeed, the folds must represent the same duration, in order to have comparable metrics across folds.",
          "Section 3.1.2.6.1 Time Series Split")

    baio = B.parent / "ir-policy-adoption-2026-10-15/evidence/08a2f88e320ec50a.json"
    saved = json.loads(baio.read_text())
    terms = ["Brier", "Gneiting", "Raftery", "logarithmic", "scoring"]
    local_check = {
        "file": str(baio.relative_to(B.parent)), "relative_to": "research/",
        "saved_artifact_sha256": sha(baio), "url": saved["url"],
        "text_terms_checked_case_insensitive": terms,
        "matches": {term: len(re.findall(re.escape(term), saved["text"], re.I)) for term in terms},
        "interpretation": "No proper-score reference found in this saved VOI page only; not a claim about all Baio publications.",
    }
    result = {"schema_version": 1, "scope": "finite_primary_source_research_only",
              "sources": sources, "quotes": quotes, "saved_baio_priority_check": local_check,
              "formula_transcription": {
                  "source_id": sources[0]["id"], "pdf_page": 5, "printed_page": 363,
                  "visual_check": "formula-page-5.png",
                  "visual_check_sha256": sha(B / "formula-page-5.png"),
                  "author_reward_brier": "S(p,i) = -sum_j(delta_ij-p_j)^2 = 2*p_i-sum_j(p_j^2)-1",
                  "author_reward_log": "S(p,i) = log(p_i)",
                  "transcription_note": "pdftotext separates summation glyphs; formulas checked visually against saved original PDF page. Loss sign and natural-log units are project conventions, not extra author investment rules.",
              }}
    (B / "sources.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    verification = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "distinct_urls": len(retrievals), "get_attempts": len(retrievals),
        "usable_sources": 2, "unavailable_sources": 1,
        "raw_hashes_verified": len(retrievals), "verbatim_quotes_verified": len(quotes),
        "network_during_build": False, "scoring_implementation_added": False,
        "parameters_or_likelihoods_estimated": False,
    }
    (B / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(verification))


if __name__ == "__main__":
    main()
