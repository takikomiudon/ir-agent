# Public capture binding v2 boundary fixes

Two reproduced P2 boundaries were corrected without changing the native format:

- Output bytes are decoded only after their declared SHA/count match. Tampered invalid UTF-8 produces a mismatch report; comparisons that depend on those untrusted bytes stay unknown.
- Common implementation shape/name/version/SHA validation precedes unknown-profile dispatch. Unknown profile parameters are not interpreted or replayed.

The targeted suite passed **41 tests** (existing 39 plus two regression methods) in 0.178 seconds. See `target-v2.log`, `implementation-v2.json` and `manifest-v2.json`; complete final bytes are in `source-after-v2/`. Editing is stopped for independent review.

All 18 pre-existing evidence files, including frozen v1 copies and findings, were unchanged. Legacy verifier functions have identical ASTs, all three saved legacy reports are exactly equal, and models/common/legacy tests are byte-identical to their saved baseline. No GET, actual DB access, external send or full-suite run occurred.

Matching remains a caller-declaration consistency result. Raw input is still required/nonnull. Extraction replay, identity, citation meaning, financial adoption, public-release time and DB first-save remain unverified/not performed; no old source was retagged.
