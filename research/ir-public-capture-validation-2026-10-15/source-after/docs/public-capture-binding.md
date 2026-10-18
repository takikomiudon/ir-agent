# Native public-capture binding (version 1)

This optional offline audit checks that one declared source, transport record and
saved artifacts agree. It does not establish that an issuer published the file,
that an extractor produced correct text, or that a financial interpretation is
valid. No network, extraction tool, database, migration or write is invoked.

The existing provider-based verifier remains the default:

```bash
python scripts/verify_case_source_bundle.py SOURCE_BUNDLE.json --repository-root ROOT
```

The new path is explicit:

```bash
python scripts/verify_case_source_bundle.py BINDING.json --repository-root ROOT --capture-binding
```

Python callers can use
`verify_public_capture_binding(binding_path, *, repository_root)` from the same
script. Unknown native formats or positive integer versions return `unknown`;
they never fall back to a familiar provider. Without the opt-in flag, the legacy
API and its result fields remain unchanged.

## Native declaration

The outer sidecar has exactly these fields:

```json
{
  "format": "ir-public-source-binding",
  "version": 1,
  "case_root": "research/new-native-case",
  "source": {
    "artifact": {"path": "source-bundle.json", "sha256": "<lowercase SHA256>", "byte_count": 123},
    "pointer": "/sources/0",
    "snapshot_sha256": "<SHA256 of original selected source using models.json_text UTF-8>",
    "snapshot_hash_profile": "ir_agent.models.json_text/UTF-8"
  },
  "transport": {
    "artifact": {"path": "capture.json", "sha256": "<lowercase SHA256>", "byte_count": 456},
    "record_pointer": "/records/0"
  }
}
```

The hashes/counts above are template placeholders, not a runnable artifact.
A coherent synthetic example and the complete required-field lists are in
[the design](../research/ir-public-capture-validation-2026-10-15/design-v1.json).
The source snapshot hash is calculated from the selected original JSON object
**before** `validate_source` fills any defaults. That representation is the
project's `models.json_text`, not a claim of RFC8785. Source IDs are not derived
or checked. The hash belongs to the external sidecar, avoiding self-reference
inside the source metadata.

Each selected native transport record has exactly `format`, `version`,
`request`, `response`, `artifacts`, and `extraction`:

- `format` is `ir-public-response-capture`, with integer `version: 1`.
- `request` contains `method: GET`, `url`, configured/prepared user agents and
  offset-aware `started_at`.
- `response` contains `url`, `status_code`, strict-boolean `complete_body`,
  nullable `error`, aware/null `headers_received_at` and `body_completed_at`,
  `body_representation`, and nullable decimal-text `content_length_header`.
- `artifacts` contains `raw` and `extracted_text`. Each nonnull artifact requires
  a relative `path`, lowercase SHA256 and integer `byte_count >= 0`.
- `extraction` contains `profile`, `implementation`, `parameters`, and `text`.
  A profile has `name` and positive integer `version`; implementation has
  `name`, `version`, and nullable SHA256. These describe the claimed extractor;
  its executable, source code and output are not replayed or authenticated.

A successful source binding requires HTTP200, complete body, no transport error,
nonnull header/body completion and extracted output. Well-typed unsuccessful
records return `mismatch` for success binding, even if their saved bytes agree.
They can have null header/body timestamps, extraction and output when absent;
missing or wrongly typed required schema fields are validation errors.
An incomplete body with a claimed completion cannot pass.

Version 1 only binds `public_disclosure` sources to
`response_entity_after_content_decoding`. `wire_capture` is a recognized but
out-of-scope representation and remains `unknown`; it is never silently treated
as an HTTP response entity. `Content-Length` is informational and is not the
saved byte count: decompression can change that count. Other valid source types
also remain outside this first scope.

## Pointers, paths and bytes

Pointers follow RFC6901: empty string selects root; `~0` and `~1` decode once,
without percent decoding. Empty object keys and keys such as `01` and `-` are
ordinary object keys. Array indices must be `0` or a nonzero ASCII integer with
no leading zero; `-`, negative, decimal and leading-zero indices are rejected.
Missing valid keys/indices are `unknown`. Malformed syntax is a validation error.
The full pinned JSON artifact rejects duplicate keys and nonfinite numbers,
including unselected siblings. No recursive search for a convenient field occurs.

`case_root` is explicit and repository-relative. Every artifact is relative to
that root. Absolute paths, parent traversal, NUL and symlink escapes are rejected
before reading the target. No bundle-parent fallback or path guessing occurs.
Artifacts must match their declared SHA/count before their records are trusted.
Missing declared files remain `unknown`; a real zero-byte file stays zero.
Files are assumed stable during the audit; this does not add filesystem locks or
race-resistant file-descriptor handling.

The saved extraction must be strict UTF-8. Its original bytes must equal both
native `extraction.text.encode('utf-8')` and `source.content.encode('utf-8')`.
CRLF, LF, BOM and form-feed bytes are not silently rewritten. Raw-to-output
transformation is not replayed, so even a matching declaration cannot prove that
text was extracted correctly from the raw file.

## Profiles and clocks

Recognized profile declarations are:

| Name/version | Required parameters |
|---|---|
| `plain_utf8_preserve` / 1 | decoder `utf-8`, BOM `preserve`, line_endings `preserve` |
| `html_visible_nodes_lf` / 1 | decoder `utf-8` or `utf-8-sig`, ignored_elements `[script, style]`, convert_charrefs `true`, node_whitespace `collapse`, joiner `LF`, terminal_LF `true` |
| `pdftotext_layout` / 1 | arguments `[-layout]`, output_encoding `UTF-8`, form_feeds `preserve`, page_numbering `one_based` |

Known parameter shapes are checked; unknown profile names/versions are
`unknown`. A recognized declaration does not verify the implementation or run
it. `extractor_reproduction` remains `not_performed` for every result.

Timestamp comparisons use aware datetime instants, so equivalent UTC and +09:00
representations agree. Started <= headers <= body-completed must hold, and source
retrieval must equal body completion. No DB first-save receipt or public release
time is inferred. These clocks are caller claims whose internal agreement is
checked; the audit is not independent proof of historical occurrence or a
historical-availability gate.

## Results and limits

Results separate format support, declared artifact bytes, transport/source
binding and profile declaration. A known mismatch wins over unknown; `matched`
only means the declared bytes and supported fields agree. The corresponding
boolean is true/false/null for matched/mismatch/unknown. Malformed recognized
schema raises a generic `ValueError`; CLI exit2 reports validation errors, exit1
reports mismatches, and exit0 means an audit completed, including `unknown`.

Native reports and errors omit URL/header/error values and original/extracted
text. They contain only paths, hashes, counts and generic field reason codes.
Source-ID derivation, extraction replay, citation bytes/meaning, issuer
identity/authenticity, financial meaning, current collection permission and DB
first-save verification are all explicitly `not_performed`.

This format is for deliberately emitted new captures. Existing Anritsu or other
legacy source/capture JSON, IDs and timestamps are not tagged, migrated or
rewritten. A new sidecar is not evidence that a historical collector already used
this format. No investment input, forecast, permission to fetch, IR message or
classification follows from `matched`.
