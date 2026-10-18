"""SQLite persistence with immutable records and compare-and-swap thesis versions."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from .models import available, json_text, now_iso, source_origins, timestamp

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS companies (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS position_observations (
    id INTEGER PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
    observed_at TEXT NOT NULL, held INTEGER NOT NULL CHECK(held IN (0,1))
);
CREATE INDEX IF NOT EXISTS position_observation_times
    ON position_observations(company_id,observed_at,id);
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
    content_hash TEXT NOT NULL, data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS theses (
    company_id TEXT NOT NULL REFERENCES companies(id), version INTEGER NOT NULL,
    data TEXT NOT NULL, PRIMARY KEY(company_id, version)
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
    signature TEXT NOT NULL UNIQUE, priority INTEGER NOT NULL, status TEXT NOT NULL,
    packet TEXT NOT NULL, lease_owner TEXT, lease_until TEXT, attempts INTEGER NOT NULL DEFAULT 0,
    result TEXT, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
    topic TEXT NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL, sent_at TEXT,
    closed_at TEXT, closure_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_open_question_per_topic
    ON questions(company_id, topic) WHERE status IN ('draft', 'awaiting_reply');
CREATE TABLE IF NOT EXISTS replies (
    id TEXT PRIMARY KEY, question_id TEXT NOT NULL REFERENCES questions(id), data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluations (
    reply_id TEXT NOT NULL REFERENCES replies(id), version INTEGER NOT NULL,
    data TEXT NOT NULL, PRIMARY KEY(reply_id, version)
);
CREATE TABLE IF NOT EXISTS decision_policies (
    id TEXT NOT NULL, version INTEGER NOT NULL, data TEXT NOT NULL,
    first_saved_at TEXT NOT NULL, PRIMARY KEY(id,version)
);
CREATE TABLE IF NOT EXISTS decision_reviews (
    id TEXT PRIMARY KEY, reply_id TEXT NOT NULL REFERENCES replies(id),
    company_id TEXT NOT NULL REFERENCES companies(id), thesis_version INTEGER NOT NULL,
    policy_id TEXT NOT NULL, policy_version INTEGER NOT NULL, data TEXT NOT NULL,
    first_saved_at TEXT NOT NULL,
    FOREIGN KEY(company_id,thesis_version) REFERENCES theses(company_id,version),
    FOREIGN KEY(policy_id,policy_version) REFERENCES decision_policies(id,version)
);
CREATE TABLE IF NOT EXISTS source_reviews (
    source_id TEXT NOT NULL REFERENCES sources(id), job_id TEXT NOT NULL REFERENCES jobs(id),
    PRIMARY KEY(source_id, job_id)
);
"""


class Store:
    def __init__(self, path: str | Path):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self._record_write_sequence = 0
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(SCHEMA)
        from .information_review import SCHEMA as INFORMATION_REVIEW_SCHEMA
        self.connection.executescript(INFORMATION_REVIEW_SCHEMA)
        from .observation_store import SCHEMA as OBSERVATION_SCHEMA
        self.connection.executescript(OBSERVATION_SCHEMA)
        from .prediction_store import SCHEMA as PREDICTION_SCHEMA
        self.connection.executescript(PREDICTION_SCHEMA)
        from .evaluation_protocols import SCHEMA as EVALUATION_PROTOCOLS_SCHEMA
        self.connection.executescript(EVALUATION_PROTOCOLS_SCHEMA)
        from .intake import SCHEMA as INTAKE_SCHEMA
        self.connection.executescript(INTAKE_SCHEMA)
        from .job_attempts import SCHEMA as JOB_ATTEMPTS_SCHEMA
        self.connection.executescript(JOB_ATTEMPTS_SCHEMA)
        from .job_requests import SCHEMA as JOB_REQUESTS_SCHEMA
        self.connection.executescript(JOB_REQUESTS_SCHEMA)
        from .availability import SCHEMA as AVAILABILITY_SCHEMA, RecordAvailability
        self.connection.executescript(AVAILABILITY_SCHEMA)
        row = self.connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if row and row["value"] != "1":
            raise ValueError("Unsupported database schema version")
        self.connection.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version','1')")
        # Existing databases have no position history. Observe their current
        # state now; never pretend that it was already known in the past.
        with self.transaction():
            self.availability_migration_issues = []
            for company in self.companies():
                self.observe_position(company["id"], company["held"])
            # Presence now is a known-by bound, never a reconstructed first save.
            observed = now_iso()
            ledger = RecordAvailability(self.connection)
            for kind, table, id_column, version_column in (
                    ('source', 'sources', 'id', None), ('thesis', 'theses', 'company_id', 'version'),
                    ('reply', 'replies', 'id', None), ('question', 'questions', 'id', None)):
                for old in self.connection.execute('SELECT * FROM ' + table).fetchall():
                    presence = ledger.observe_existing(kind, old[id_column], json.loads(old['data']),
                                                       version=old[version_column] if version_column else None, now=observed)
                    if presence.get('status') == 'unknown':
                        self.availability_migration_issues.append(presence)

    def close(self) -> None:
        self.connection.close()

    @contextmanager
    def transaction(self):
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise
        else:
            self.connection.execute("COMMIT")

    @contextmanager
    def _record_write(self):
        """Keep a record and its presence receipt atomic, including nested use."""
        nested = self.connection.in_transaction
        self._record_write_sequence += 1
        point = 'record_write_' + str(self._record_write_sequence)
        self.connection.execute('SAVEPOINT ' + point if nested else 'BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            if nested:
                self.connection.execute('ROLLBACK TO SAVEPOINT ' + point)
                self.connection.execute('RELEASE SAVEPOINT ' + point)
            else:
                self.connection.execute('ROLLBACK')
            raise
        else:
            self.connection.execute('RELEASE SAVEPOINT ' + point if nested else 'COMMIT')

    @staticmethod
    def _clock(now=None):
        value = now.isoformat() if hasattr(now, 'isoformat') else now
        return timestamp(now_iso() if value is None else value, 'trusted runtime clock').isoformat()

    def company(self, company_id: str) -> dict:
        row = self.connection.execute("SELECT data FROM companies WHERE id=?", (company_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown company: {company_id}")
        return json.loads(row["data"])

    def companies(self) -> list[dict]:
        return [json.loads(r["data"]) for r in self.connection.execute("SELECT data FROM companies ORDER BY id")]

    def put_company(self, company: dict) -> None:
        existing = self.connection.execute("SELECT data FROM companies WHERE id=?", (company["id"],)).fetchone()
        if existing:
            # Provider refreshes must not reactivate excluded companies or erase holdings.
            prior = json.loads(existing["data"])
            for key in ("status", "screening_reason", "held"):
                if key in prior:
                    company[key] = prior[key]
            if "ir_contact" not in company and "ir_contact" in prior:
                company["ir_contact"] = prior["ir_contact"]
        self.connection.execute(
            "INSERT INTO companies VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
            (company["id"], json_text(company)),
        )
        self.observe_position(company["id"], company["held"])

    def observe_position(self, company_id: str, held: bool) -> None:
        """Record a state when it is actually observed, in the caller's transaction."""
        if type(held) is not bool:
            raise ValueError("Observed position must be boolean")
        prior = self.connection.execute(
            "SELECT held FROM position_observations WHERE company_id=? ORDER BY observed_at DESC,id DESC LIMIT 1",
            (company_id,),
        ).fetchone()
        if prior is None or bool(prior["held"]) != held:
            self.connection.execute(
                "INSERT INTO position_observations(company_id,observed_at,held) VALUES (?,?,?)",
                (company_id, now_iso(), int(held)),
            )

    def position_at(self, company_id: str, as_of: str) -> dict | None:
        boundary = timestamp(as_of).isoformat()
        row = self.connection.execute(
            "SELECT id,observed_at,held FROM position_observations WHERE company_id=? AND observed_at<=? "
            "ORDER BY observed_at DESC,id DESC LIMIT 1", (company_id, boundary),
        ).fetchone()
        if row is None:
            return None
        return {"company_id": company_id, "held": bool(row["held"]), "observed_at": row["observed_at"],
                "observation_id": row["id"], "kind": "observed"}

    def sources(self, company_id: str) -> list[dict]:
        return [json.loads(r["data"]) for r in self.connection.execute(
            "SELECT data FROM sources WHERE company_id=? ORDER BY id", (company_id,)
        )]

    def source(self, source_id: str) -> dict:
        row = self.connection.execute("SELECT data FROM sources WHERE id=?", (source_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown source: {source_id}")
        return json.loads(row["data"])

    def put_source(self, source: dict, *, now=None) -> bool:
        with self._record_write():
            return self._put_source(source, now=self._clock(now))

    def _put_source(self, source: dict, *, now) -> bool:
        encoded = json_text(source)
        existing = self.connection.execute("SELECT data FROM sources WHERE id=?", (source["id"],)).fetchone()
        if existing:
            old = json.loads(existing["data"])
            comparable = dict(source)
            comparable["retrieved_at"] = old["retrieved_at"]
            if json_text(comparable) != json_text(old):
                raise ValueError(f"Source id reused for different evidence: {source['id']}")
            if timestamp(source["retrieved_at"]) < timestamp(old["retrieved_at"]):
                raise ValueError("Cannot backdate a source's first retrieval")
            return False
        digest = sha256(source["content"].encode()).hexdigest()
        self.connection.execute("INSERT INTO sources VALUES (?,?,?,?)", (
            source["id"], source["company_id"], digest, encoded,
        ))
        from .availability import RecordAvailability
        RecordAvailability(self.connection).record_first_save('source', source['id'], source, now=now)
        return True

    def thesis(self, company_id: str, *, as_of=None, now=None) -> dict | None:
        if as_of is not None:
            return self.thesis_view(company_id, as_of=as_of, knowledge_at=as_of, mode='pit', now=now)['record']
        rows = self.connection.execute(
            "SELECT data FROM theses WHERE company_id=? ORDER BY version DESC", (company_id,)
        )
        for row in rows:
            result = json.loads(row["data"])
            return result
        return None

    def source_availability(self, source: dict, *, as_of, knowledge_at=None, now=None) -> dict:
        """Check both clocks throughout the saved source DAG; do not alter data."""
        from .availability import RecordAvailability
        target = timestamp(as_of.isoformat() if hasattr(as_of, 'isoformat') else as_of)
        known = timestamp(knowledge_at.isoformat() if hasattr(knowledge_at, 'isoformat') else knowledge_at) if knowledge_at is not None else target
        clock = self._clock(now)
        if max(target, known) > timestamp(clock):
            raise ValueError('Historical cutoffs cannot be after the trusted runtime clock')
        ledger = RecordAvailability(self.connection)
        checks, active, visited = [], set(), set()
        company_id = source['company_id']

        def visit(item):
            identity = item['id']
            if identity in active:
                checks.append({'source_id': identity, 'available': False, 'reason_codes': ['source_origin_cycle']})
                return
            if identity in visited:
                return
            active.add(identity)
            if item['company_id'] != company_id:
                checks.append({'source_id': identity, 'available': False, 'reason_codes': ['source_origin_company_mismatch']})
            else:
                try:
                    declared_available = available(item, target)
                except (ValueError, TypeError, OverflowError):
                    checks.append({'source_id': identity, 'available': None, 'reason_codes': ['invalid_effective_time']})
                else:
                    if not declared_available:
                        checks.append({'source_id': identity, 'available': False, 'reason_codes': ['source_not_available_at_target_time']})
                    else:
                        check = ledger.at('source', identity, item, as_of=target.isoformat(),
                                          knowledge_at=known.isoformat(), now=clock)
                        checks.append({'source_id': identity, **check})
            for parent_id in source_origins(item):
                try:
                    parent = self.source(parent_id)
                except ValueError:
                    checks.append({'source_id': parent_id, 'available': None, 'reason_codes': ['source_origin_missing']})
                else:
                    visit(parent)
            active.remove(identity)
            visited.add(identity)

        visit(source)
        flags = [item['available'] for item in checks]
        state = False if any(value is False for value in flags) else (None if any(value is None for value in flags) else True)
        return {'available': state, 'checks': checks,
                'reason_codes': sorted({reason for check in checks for reason in check.get('reason_codes', [])})}

    def source_available(self, source: dict, *, as_of, knowledge_at=None, now=None) -> bool:
        return self.source_availability(source, as_of=as_of, knowledge_at=knowledge_at, now=now)['available'] is True

    def thesis_view(self, company_id: str, *, as_of, knowledge_at, mode: str, now=None) -> dict:
        from .availability import RecordAvailability
        target = timestamp(as_of.isoformat() if hasattr(as_of, 'isoformat') else as_of)
        known = timestamp(knowledge_at.isoformat() if hasattr(knowledge_at, 'isoformat') else knowledge_at)
        if mode not in {'pit', 'retrospective'} or (mode == 'pit' and target != known):
            raise ValueError('PIT requires equal as_of and knowledge_at; retrospective requires an explicit mode')
        clock = self._clock(now)
        if max(target, known) > timestamp(clock):
            raise ValueError('Historical cutoffs cannot be after the trusted runtime clock')
        ledger = RecordAvailability(self.connection)
        chosen, selected_availability, excluded, unknown = None, None, [], False
        for row in self.connection.execute('SELECT data FROM theses WHERE company_id=? ORDER BY version DESC', (company_id,)):
            value = json.loads(row['data'])
            check = ledger.at('thesis', company_id, value, version=value['version'],
                              as_of=target.isoformat(), knowledge_at=known.isoformat(), now=clock)
            source_checks = []
            if check['available'] is True:
                for identity in value['evidence_ids']:
                    try:
                        evidence = self.source(identity)
                    except ValueError:
                        source_checks.append({'available': None, 'reason_codes': ['thesis_evidence_missing'], 'source_id': identity})
                    else:
                        if evidence['company_id'] != company_id:
                            source_checks.append({'available': False, 'reason_codes': ['thesis_evidence_company_mismatch'], 'source_id': identity})
                        else:
                            source_checks.append(self.source_availability(evidence, as_of=target, knowledge_at=known, now=clock))
            flags = [check['available']] + [item['available'] for item in source_checks]
            if all(flag is True for flag in flags) and chosen is None:
                chosen, selected_availability = value, {'thesis': check, 'sources': source_checks}
            elif not all(flag is True for flag in flags):
                unknown = unknown or any(flag is None for flag in flags)
                excluded.append({'version': value['version'], 'availability': check, 'sources': source_checks,
                                 'reason_codes': sorted({reason for item in [check] + source_checks for reason in item.get('reason_codes', [])})})
        return {'temporal_mode': mode, 'as_of': target.isoformat(), 'knowledge_at': known.isoformat(),
                'record': chosen, 'selected_availability': selected_availability,
                'availability_status': ('partial' if chosen is not None else 'unknown') if unknown else 'known',
                'excluded': excluded, 'limitations': ['A declared record time is distinct from trusted DB presence.',
                                                      'Legacy presence is a known-by bound, not an exact first save.',
                                                      'This read-only view does not reconstruct mutable company or question states.']}

    def put_thesis(self, thesis: dict, *, now=None) -> bool:
        with self._record_write():
            return self._put_thesis(thesis, now=self._clock(now))

    def _put_thesis(self, thesis: dict, *, now) -> bool:
        company_id, version = thesis["company_id"], thesis["version"]
        self.company(company_id)
        existing = self.connection.execute(
            "SELECT data FROM theses WHERE company_id=? AND version=?", (company_id, version)
        ).fetchone()
        if existing:
            if existing["data"] != json_text(thesis):
                raise ValueError("A saved thesis version is immutable; append a new version")
            return False
        current = self.thesis(company_id)
        expected = current["version"] + 1 if current else 1
        if version != expected:
            raise ValueError(f"Stale or skipped thesis version: expected {expected}, got {version}")
        if current and timestamp(thesis["recorded_at"]) < timestamp(current["recorded_at"]):
            raise ValueError("New thesis versions cannot be backdated")
        for source_id in thesis["evidence_ids"]:
            source = self.source(source_id)
            if source["company_id"] != company_id:
                raise ValueError("Thesis evidence belongs to another company")
            if timestamp(source["retrieved_at"]) > timestamp(thesis["recorded_at"]):
                raise ValueError("Thesis cites evidence not yet retrieved")
        self.connection.execute("INSERT INTO theses VALUES (?,?,?)", (company_id, version, json_text(thesis)))
        from .availability import RecordAvailability
        RecordAvailability(self.connection).record_first_save('thesis', company_id, thesis, version=version, now=now)
        return True

    def job(self, job_id: str) -> dict:
        row = self.connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown job: {job_id}")
        result = dict(row)
        result["packet"] = json.loads(result["packet"])
        if result["result"] is not None:
            result["result"] = json.loads(result["result"])
        return result

    def question(self, question_id: str) -> dict:
        row = self.connection.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown question: {question_id}")
        result = json.loads(row["data"])
        result.update(status=row["status"], sent_at=row["sent_at"],
                      closed_at=row["closed_at"], closure_reason=row["closure_reason"])
        return result

    def reply(self, reply_id: str) -> dict:
        row = self.connection.execute("SELECT data FROM replies WHERE id=?", (reply_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown reply: {reply_id}")
        return json.loads(row["data"])

    def decision_policy(self, policy_id: str, version: int) -> dict:
        row = self.connection.execute("SELECT data FROM decision_policies WHERE id=? AND version=?", (policy_id, version)).fetchone()
        if row is None:
            raise ValueError("Unknown decision policy version")
        return json.loads(row["data"])

    def decision_policy_saved_at(self, policy_id: str, version: int) -> str:
        row = self.connection.execute("SELECT first_saved_at FROM decision_policies WHERE id=? AND version=?", (policy_id, version)).fetchone()
        if row is None:
            raise ValueError("Unknown decision policy version")
        return row["first_saved_at"]

    def put_decision_policy(self, policy: dict, saved_at: str) -> bool:
        existing = self.connection.execute("SELECT data FROM decision_policies WHERE id=? AND version=?", (policy["id"], policy["version"])).fetchone()
        if existing:
            if existing["data"] != json_text(policy):
                raise ValueError("A saved decision policy version is immutable")
            return False
        latest = self.connection.execute("SELECT version,data FROM decision_policies WHERE id=? ORDER BY version DESC LIMIT 1", (policy["id"],)).fetchone()
        if policy["version"] != (latest["version"] + 1 if latest else 1):
            raise ValueError("Decision policy versions must be consecutive")
        if latest and timestamp(policy["recorded_at"]) < timestamp(json.loads(latest["data"])["recorded_at"]):
            raise ValueError("Decision policy versions cannot be backdated")
        self.connection.execute("INSERT INTO decision_policies VALUES (?,?,?,?)", (policy["id"], policy["version"], json_text(policy), saved_at))
        return True

    def decision_review(self, review_id: str) -> dict:
        row = self.connection.execute("SELECT data FROM decision_reviews WHERE id=?", (review_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown decision review")
        return json.loads(row["data"])

    def decision_review_for_request(self, request: dict) -> dict | None:
        digest = sha256(json_text(request).encode()).hexdigest()
        rows = self.connection.execute("SELECT data FROM decision_reviews WHERE reply_id=?", (request["reply_id"],))
        for row in rows:
            value = json.loads(row["data"])
            if value.get("review_request_sha256") == digest:
                return value
        return None

    def put_decision_review(self, review: dict, saved_at: str) -> bool:
        existing = self.connection.execute("SELECT data FROM decision_reviews WHERE id=?", (review["id"],)).fetchone()
        if existing:
            if existing["data"] != json_text(review):
                raise ValueError("A saved decision review is immutable")
            return False
        self.connection.execute("INSERT INTO decision_reviews VALUES (?,?,?,?,?,?,?,?)", (
            review["id"], review["reply_id"], review["company_id"], review["thesis_version"],
            review["policy_id"], review["policy_version"], json_text(review), saved_at))
        return True
