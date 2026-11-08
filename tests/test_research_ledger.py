#!/usr/bin/env python3
"""Unit tests for the research ledger: keys, revisions, strict records, lookup and migration.

Standard library only; every test uses a temporary database and no network.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
# Loading the module from the skill folder must not leave a __pycache__ there.
sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location(
    "research_ledger",
    ROOT / "plugins/product-docs-and-research/skills/101-research-ledger/scripts/research_ledger.py")
research_ledger = importlib.util.module_from_spec(_SPEC)
sys.modules["research_ledger"] = research_ledger
_SPEC.loader.exec_module(research_ledger)


class BaseTempDirTestCase(unittest.TestCase):
    """Test case setup creating isolated temp dirs."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "ledger.db")
        self.stats_path = os.path.join(self.tmpdir.name, "stats.json")

        self.orig_env = os.environ.copy()
        os.environ['RESEARCH_LEDGER_DB'] = self.db_path
        os.environ['RESEARCH_LEDGER_STATS'] = self.stats_path

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        self.tmpdir.cleanup()


class TestFreshnessAndDateArithmetic(BaseTempDirTestCase):
    """Tests for section 3.2 freshness rules and date arithmetic."""

    def test_volatile_ttl_14_days(self):
        today = date(2026, 11, 7)
        raw = {
            "kind": "research",
            "question": "What is the latest pricing for Claude 3.5 Sonnet?",
            "topic": "ai/pricing",
            "researched_on": today.isoformat(),
            "freshness": "volatile"
        }
        norm = research_ledger.validate_and_normalize_record(raw)
        self.assertEqual(norm["freshness"], "volatile")
        self.assertEqual(norm["researched_on"], "2026-11-07")
        self.assertEqual(norm["valid_until"], "2026-11-21")  # +14 days

    def test_moderate_ttl_28_days(self):
        today = date(2026, 11, 7)
        raw = {
            "kind": "research",
            "question": "How do tool comparisons between Tailscale and Wireguard look?",
            "topic": "networking/vpn",
            "researched_on": today.isoformat(),
            "freshness": "moderate"
        }
        norm = research_ledger.validate_and_normalize_record(raw)
        self.assertEqual(norm["freshness"], "moderate")
        self.assertEqual(norm["valid_until"], "2026-12-05")  # +28 days

    def test_stable_ttl_90_days(self):
        today = date(2026, 11, 7)
        raw = {
            "kind": "research",
            "question": "What is the RFC specification for HTTP/2 multiplexing?",
            "topic": "protocols/http2",
            "researched_on": today.isoformat(),
            "freshness": "stable"
        }
        norm = research_ledger.validate_and_normalize_record(raw)
        self.assertEqual(norm["freshness"], "stable")
        self.assertEqual(norm["valid_until"], "2027-02-05")  # 7 Nov 2026 + 90 days

    def test_missing_freshness_defaults_to_moderate_and_unknown_rejected(self):
        raw_missing = {
            "question": "General question",
            "topic": "misc",
        }
        norm = research_ledger.validate_and_normalize_record(raw_missing)
        self.assertEqual(norm["freshness"], "moderate")
        r_date = date.fromisoformat(norm["researched_on"])
        v_date = date.fromisoformat(norm["valid_until"])
        self.assertEqual((v_date - r_date).days, 28)

        raw_unknown = {
            "question": "General question",
            "topic": "misc",
            "freshness": "unknown-freshness",
        }
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record(raw_unknown)


class TestRecordValidation(BaseTempDirTestCase):
    """Tests for section 3.1 strict record validation."""

    def test_valid_full_record(self):
        raw = {
            "kind": "research",
            "question": "How does Tailscale Taildrive work?",
            "topic": "tailscale/taildrive",
            "researched_on": "2026-11-07",
            "freshness": "volatile",
            "projects": ["skillry-caarimu"],
            "plan_items": ["C2"],
            "client": "claude",
            "findings": [
                {"claim": "Taildrive shares folders over WebDAV", "class": "vendor", "source_ids": ["s1"], "as_of": "2026-11-07"}
            ],
            "sources": [
                {"id": "s1", "url": "https://tailscale.com/blog/taildrive", "title": "Taildrive", "publisher": "Tailscale"}
            ],
            "contradictions": [],
            "open_questions": ["Is write concurrency safe?"],
            "supersedes": "research/tailscale/taildrive/old-version",
            "confidence": "high"
        }
        norm = research_ledger.validate_and_normalize_record(raw)
        self.assertEqual(norm["kind"], "research")
        self.assertEqual(norm["supersedes"], "research/tailscale/taildrive/old-version")
        self.assertEqual(norm["confidence"], "high")
        self.assertEqual(norm["evidence"], "verified")
        self.assertEqual(norm["revision"], 1)
        self.assertEqual(len(norm["findings"]), 1)
        self.assertEqual(norm["findings"][0]["class"], "vendor")

    def test_missing_question_fails(self):
        raw = {
            "kind": "research",
            "topic": "test",
            "freshness": "moderate"
        }
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record(raw)

    def test_missing_topic_fails(self):
        raw = {
            "kind": "research",
            "question": "What is life?",
            "freshness": "moderate"
        }
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record(raw)

    def test_invalid_kind_fails(self):
        raw = {
            "kind": "not_research",
            "question": "Valid question?",
            "topic": "test"
        }
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record(raw)

    def test_strict_validation_rejections(self):
        """Test (c): bad date, future date, unknown class, unknown source id, fact without source and duplicate source id are each rejected."""
        today_utc = datetime.now(timezone.utc).date()

        # 1. Bad researched_on date
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "researched_on": "not-an-iso-date",
            })

        # 2. Future researched_on date (> today UTC + 1 day)
        future_date = (today_utc + timedelta(days=3)).isoformat()
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "researched_on": future_date,
            })

        # 3. Bad or future finding as_of date
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "s1"}],
                "findings": [{"claim": "C", "class": "vendor", "source_ids": ["s1"], "as_of": "bad-date"}],
            })
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "s1"}],
                "findings": [{"claim": "C", "class": "vendor", "source_ids": ["s1"], "as_of": future_date}],
            })

        # 4. Unknown finding class (and verify missing class defaults to 'inference', never 'fact')
        norm_default_class = research_ledger.validate_and_normalize_record({
            "question": "Q?",
            "topic": "t",
            "findings": [{"claim": "Uncited inference claim"}],
        })
        self.assertEqual(norm_default_class["findings"][0]["class"], "inference")
        self.assertEqual(norm_default_class["evidence"], "draft")

        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "s1"}],
                "findings": [{"claim": "C", "class": "unknown_class", "source_ids": ["s1"]}],
            })

        # 5. Unknown confidence
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "confidence": "certain",
            })

        # 6. Unknown source_id in finding
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "s1"}],
                "findings": [{"claim": "C", "class": "vendor", "source_ids": ["s_missing"]}],
            })

        # 7. Finding of class 'fact' without source_id
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "s1"}],
                "findings": [{"claim": "C", "class": "fact", "source_ids": []}],
            })

        # 8. Duplicate source id (and empty source id)
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "s1"}, {"id": "s1"}],
            })
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "sources": [{"id": "   "}],
            })

        # 9. Input claiming evidence='verified' when record only qualifies as 'draft'
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record({
                "question": "Q?",
                "topic": "t",
                "evidence": "verified",
            })


class TestReviewStateAndStructure(BaseTempDirTestCase):
    """Review F01 recheck: an explicit draft stays a draft and an id alone is not a source."""

    def record(self, **overrides):
        base = {"question": "How long does the cache live?", "topic": "cache/ttl",
                "findings": [{"claim": "Entries live 5 minutes", "class": "vendor", "source_ids": ["s1"]}],
                "sources": [{"id": "s1", "url": "https://example.org/cache"}]}
        base.update(overrides)
        return base

    def test_an_explicit_draft_stays_a_draft(self):
        norm = research_ledger.validate_and_normalize_record(self.record(evidence="draft"))
        self.assertEqual(norm["evidence"], "draft")
        self.assertTrue(norm["structure_complete"])

    def test_a_source_without_url_path_or_artifact_keeps_the_record_a_draft(self):
        norm = research_ledger.validate_and_normalize_record(self.record(sources=[{"id": "s1"}]))
        self.assertEqual(norm["evidence"], "draft")
        self.assertFalse(norm["structure_complete"])
        for locator in ({"path": "evidence/cache.md"}, {"artifact": "receipt-42"}):
            norm = research_ledger.validate_and_normalize_record(self.record(sources=[{"id": "s1", **locator}]))
            self.assertEqual(norm["evidence"], "verified")

    def test_verified_is_refused_without_a_locator(self):
        with self.assertRaises(ValueError):
            research_ledger.validate_and_normalize_record(self.record(sources=[{"id": "s1"}], evidence="verified"))

    def test_migration_keeps_drafts_and_unlocated_sources_as_drafts(self):
        state, reasons = research_ledger._evaluate_record_for_migration(self.record(evidence="draft"))
        self.assertEqual(state, "draft")
        self.assertTrue(any("draft" in r for r in reasons))
        state, reasons = research_ledger._evaluate_record_for_migration(self.record(sources=[{"id": "s1"}]))
        self.assertEqual(state, "draft")
        self.assertTrue(any("no url, path or artifact" in r for r in reasons))


class TestKeysAndRevisions(BaseTempDirTestCase):
    """Tests for section 1 hashed topic keys and revision tracking."""

    def test_two_questions_sharing_first_60_chars_stored_as_two_rows(self):
        """Test (a): two questions sharing the first 60 characters are stored as two rows."""
        prefix = "How do we configure distributed connection pooling and failover "
        self.assertGreaterEqual(len(prefix), 60)
        q1 = prefix + "in PostgreSQL cluster mode alpha?"
        q2 = prefix + "in PostgreSQL cluster mode beta?"
        self.assertEqual(q1[:60], q2[:60])

        k1 = research_ledger.make_topic_key("databases/postgres", q1)
        k2 = research_ledger.make_topic_key("databases/postgres", q2)
        self.assertNotEqual(k1, k2)
        self.assertRegex(k1, r"^research/databases/postgres/[a-z0-9-]+--[0-9a-f]{12}$")
        self.assertRegex(k2, r"^research/databases/postgres/[a-z0-9-]+--[0-9a-f]{12}$")

        expected_h12 = hashlib.sha256(
            f"{research_ledger.normalize('databases/postgres')}\n{research_ledger.normalize(q1)}".encode("utf-8")
        ).hexdigest()[:12]
        self.assertTrue(k1.endswith(f"--{expected_h12}"))

        research_ledger.save_record({
            "question": q1,
            "topic": "databases/postgres",
            "sources": [{"id": "s1", "url": "https://postgresql.org/a"}],
            "findings": [{"claim": "Alpha configuration detail", "class": "fact", "source_ids": ["s1"]}],
        })
        research_ledger.save_record({
            "question": q2,
            "topic": "databases/postgres",
            "sources": [{"id": "s1", "url": "https://postgresql.org/b"}],
            "findings": [{"claim": "Beta configuration detail", "class": "fact", "source_ids": ["s1"]}],
        })

        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT topic_key, question FROM research_records ORDER BY topic_key").fetchall()
        conn.close()
        self.assertEqual(len(rows), 2)
        self.assertEqual({r[1] for r in rows}, {q1, q2})

    def test_saving_same_question_twice_creates_revisions_and_preserves_created_at(self):
        """Test (b): saving the same question twice gives one row with revision 2 and two rows in research_revisions."""
        res1 = research_ledger.save_record({
            "question": "What is SQLite WAL mode?",
            "topic": "databases/sqlite",
            "sources": [{"id": "s1", "url": "https://sqlite.org/wal.html"}],
            "findings": [{"claim": "First revision claim", "class": "fact", "source_ids": ["s1"]}],
        })
        self.assertEqual(res1["record"]["revision"], 1)

        conn = sqlite3.connect(self.db_path)
        created_1, updated_1 = conn.execute(
            "SELECT created_at, updated_at FROM research_records WHERE topic_key = ?",
            (res1["topic_key"],),
        ).fetchone()
        conn.close()

        # Save again with whitespace/case differences that normalize to the same question
        res2 = research_ledger.save_record({
            "question": "  what is   SQLite WAL mode? ",
            "topic": "Databases/SQLite",
            "sources": [{"id": "s1", "url": "https://sqlite.org/wal.html"}],
            "findings": [{"claim": "Second revision updated claim", "class": "fact", "source_ids": ["s1"]}],
        })
        self.assertEqual(res2["topic_key"], res1["topic_key"])
        self.assertEqual(res2["record"]["revision"], 2)

        conn = sqlite3.connect(self.db_path)
        main_rows = conn.execute(
            "SELECT topic_key, data_json, created_at, updated_at FROM research_records"
        ).fetchall()
        self.assertEqual(len(main_rows), 1)
        main_data = json.loads(main_rows[0][1])
        self.assertEqual(main_data["revision"], 2)
        self.assertEqual(main_data["findings"][0]["claim"], "Second revision updated claim")
        self.assertEqual(main_rows[0][2], created_1)
        self.assertGreaterEqual(main_rows[0][3], updated_1)

        rev_rows = conn.execute(
            "SELECT revision, data_json, saved_at FROM research_revisions WHERE topic_key = ? ORDER BY revision ASC",
            (res1["topic_key"],),
        ).fetchall()
        conn.close()

        self.assertEqual(len(rev_rows), 2)
        self.assertEqual(rev_rows[0][0], 1)
        self.assertEqual(json.loads(rev_rows[0][1])["revision"], 1)
        self.assertEqual(json.loads(rev_rows[0][1])["findings"][0]["claim"], "First revision claim")
        self.assertEqual(rev_rows[1][0], 2)
        self.assertEqual(json.loads(rev_rows[1][1])["revision"], 2)
        self.assertEqual(json.loads(rev_rows[1][1])["findings"][0]["claim"], "Second revision updated claim")


class TestSQLiteFallbackAndSave(BaseTempDirTestCase):
    """Tests storing records in SQLite FTS5."""

    def test_save_persists_in_sqlite_tables(self):
        raw = {
            "question": "What is SQLite WAL mode?",
            "topic": "databases/sqlite",
            "freshness": "stable",
            "sources": [{"id": "s1", "url": "https://sqlite.org/wal.html"}],
            "findings": [{"claim": "WAL mode provides concurrency for multiple readers and one writer", "class": "fact", "source_ids": ["s1"]}],
            "supersedes": "old-key"
        }
        res = research_ledger.save_record(raw)
        self.assertEqual(res["status"], "ok")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT topic_key, supersedes, question, valid_until FROM research_records")
        rows = cur.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "old-key")
        self.assertEqual(rows[0][2], "What is SQLite WAL mode?")

        cur.execute("SELECT topic_key, claims FROM research_fts")
        fts_rows = cur.fetchall()
        self.assertEqual(len(fts_rows), 1)
        self.assertIn("WAL mode provides concurrency", fts_rows[0][1])
        conn.close()

    def test_cli_save_command(self):
        record = {
            "kind": "research",
            "question": "What is Python GIL?",
            "topic": "python/runtime",
            "freshness": "moderate"
        }
        json_file = os.path.join(self.tmpdir.name, "test_record.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(record, f)

        stdout_capture = io.StringIO()
        with mock.patch("sys.stdout", stdout_capture):
            with mock.patch("sys.argv", ["research_ledger.py", "save", "--json", json_file]):
                exit_code = research_ledger.main()
                self.assertEqual(exit_code, 0)

        out = json.loads(stdout_capture.getvalue())
        self.assertEqual(out["status"], "ok")
        self.assertIn("topic_key", out)


class TestLookup(BaseTempDirTestCase):
    """Tests for section 3.3 lookup with FTS ranking and hit_fresh/hit_stale/partial/miss decisions."""

    def test_lookup_miss_when_empty(self):
        res = research_ledger.lookup_record("Non-existent topic question?")
        self.assertEqual(res["status"], "miss")
        self.assertEqual(res["records"], [])

    def test_lookup_hit_fresh(self):
        today = datetime.now(timezone.utc).date()
        record = {
            "question": "How to configure PostgreSQL connection pooling with PgBouncer?",
            "topic": "postgresql/pgbouncer",
            "researched_on": today.isoformat(),
            "freshness": "moderate",  # valid for 28 days
            "sources": [{"id": "s1", "url": "https://www.pgbouncer.org"}],
            "findings": [{"claim": "PgBouncer manages connections in transaction or session mode", "class": "fact", "source_ids": ["s1"]}]
        }
        research_ledger.save_record(record)

        res = research_ledger.lookup_record("How to configure PostgreSQL connection pooling with PgBouncer?")
        self.assertEqual(res["status"], "hit_fresh")
        self.assertEqual(len(res["records"]), 1)
        self.assertEqual(res["records"][0]["question"], record["question"])

    def test_draft_record_saves_and_lookup_returns_partial(self):
        """Test (d): a record with no findings or no sources saves as draft and a lookup that would be hit_fresh returns partial."""
        today = datetime.now(timezone.utc).date()
        q1 = "How does SQLite FTS5 BM25 ranking work internally?"
        res_no_findings = research_ledger.save_record({
            "question": q1,
            "topic": "databases/sqlite",
            "researched_on": today.isoformat(),
            "freshness": "stable",
        })
        self.assertEqual(res_no_findings["record"]["evidence"], "draft")

        lookup1 = research_ledger.lookup_record(q1)
        self.assertEqual(lookup1["status"], "partial")

        q2 = "How does PostgreSQL logical replication handle DDL changes?"
        res_no_sources = research_ledger.save_record({
            "question": q2,
            "topic": "databases/postgres",
            "researched_on": today.isoformat(),
            "freshness": "stable",
            "findings": [{"claim": "DDL is not replicated automatically", "class": "inference"}],
        })
        self.assertEqual(res_no_sources["record"]["evidence"], "draft")

        lookup2 = research_ledger.lookup_record(q2)
        self.assertEqual(lookup2["status"], "partial")

    def test_revalidate_and_current_price_turn_hit_fresh_into_hit_stale(self):
        """Test (e): revalidate and a 'current price' question turn hit_fresh into hit_stale."""
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=2)

        # 1. Revalidate flag turns a fresh verified record into hit_stale
        q_arch = "How does WireGuard key exchange protocol work?"
        research_ledger.save_record({
            "question": q_arch,
            "topic": "networking/wireguard",
            "researched_on": today.isoformat(),
            "freshness": "stable",
            "sources": [{"id": "s1", "url": "https://www.wireguard.com/protocol/"}],
            "findings": [{"claim": "Uses Noise_IKpsk2 handshake", "class": "fact", "source_ids": ["s1"]}],
        })
        self.assertEqual(research_ledger.lookup_record(q_arch)["status"], "hit_fresh")
        self.assertEqual(research_ledger.lookup_record(q_arch, revalidate=True)["status"], "hit_stale")

        # Also test --revalidate via CLI
        stdout_capture = io.StringIO()
        with mock.patch("sys.stdout", stdout_capture):
            with mock.patch("sys.argv", ["research_ledger.py", "lookup", q_arch, "--revalidate"]):
                exit_code = research_ledger.main()
                self.assertEqual(exit_code, 0)
        cli_out = json.loads(stdout_capture.getvalue())
        self.assertEqual(cli_out["status"], "hit_stale")

        # 2. A 'current price' question researched before today turns hit_fresh into hit_stale
        q_price = "What is the current price of Claude Sonnet API tokens?"
        research_ledger.save_record({
            "question": q_price,
            "topic": "ai/pricing",
            "researched_on": yesterday.isoformat(),
            "freshness": "stable",  # valid_until is +88 days in the future
            "sources": [{"id": "s1", "url": "https://anthropic.com/pricing"}],
            "findings": [{"claim": "Input tokens cost $3 per million", "class": "vendor", "source_ids": ["s1"]}],
        })
        res_price = research_ledger.lookup_record(q_price)
        self.assertEqual(res_price["status"], "hit_stale")

        # Turkish current/price keyword check ('güncel fiyatı' / 'son sürüm')
        q_tr = "Claude API güncel fiyatı ve son sürüm politikası nedir?"
        research_ledger.save_record({
            "question": q_tr,
            "topic": "ai/fiyat",
            "researched_on": yesterday.isoformat(),
            "freshness": "stable",
            "sources": [{"id": "s1", "url": "https://anthropic.com/pricing"}],
            "findings": [{"claim": "Milyon token başına 3 dolar", "class": "vendor", "source_ids": ["s1"]}],
        })
        self.assertEqual(research_ledger.lookup_record(q_tr)["status"], "hit_stale")

    def test_lookup_hit_stale(self):
        old_date = datetime.now(timezone.utc).date() - timedelta(days=60)
        record = {
            "question": "What is the newest pricing for GPT-4o?",
            "topic": "openai/pricing",
            "researched_on": old_date.isoformat(),
            "freshness": "volatile",  # valid for 14 days, so expired ~46 days ago
            "sources": [{"id": "s1", "url": "https://openai.com/api/pricing"}],
            "findings": [{"claim": "Input tokens cost $5 per million", "class": "vendor", "source_ids": ["s1"]}]
        }
        research_ledger.save_record(record)

        res = research_ledger.lookup_record("What is the newest pricing for GPT-4o?")
        self.assertEqual(res["status"], "hit_stale")
        self.assertEqual(len(res["records"]), 1)
        self.assertEqual(res["records"][0]["question"], record["question"])

    def test_lookup_partial(self):
        today = datetime.now(timezone.utc).date()
        record = {
            "question": "How to deploy Kubernetes on Google Cloud Platform?",
            "topic": "cloud/kubernetes",
            "researched_on": today.isoformat(),
            "freshness": "stable",
            "sources": [{"id": "s1", "url": "https://cloud.google.com/kubernetes-engine"}],
            "findings": [{"claim": "Use Google Kubernetes Engine (GKE) for managed clusters", "class": "fact", "source_ids": ["s1"]}]
        }
        research_ledger.save_record(record)

        # Query only partially overlaps ("Kubernetes" matches claim/question, but rest differs)
        res = research_ledger.lookup_record("How do I monitor Kubernetes CPU usage with Prometheus?")
        self.assertIn(res["status"], ("partial", "hit_fresh"))
        self.assertGreaterEqual(len(res["records"]), 1)

    def test_lookup_with_topic_filter(self):
        today = datetime.now(timezone.utc).date()
        r1 = {
            "question": "How does auth work?",
            "topic": "security/auth",
            "researched_on": today.isoformat(),
            "freshness": "stable"
        }
        r2 = {
            "question": "How does auth work?",
            "topic": "protocols/oauth",
            "researched_on": today.isoformat(),
            "freshness": "stable"
        }
        research_ledger.save_record(r1)
        research_ledger.save_record(r2)

        res = research_ledger.lookup_record("How does auth work?", topic="protocols/oauth")
        self.assertIn(res["status"], ("hit_fresh", "partial"))
        self.assertGreaterEqual(len(res["records"]), 1)
        self.assertEqual(res["records"][0]["topic"], "protocols/oauth")

    def test_lookup_max_32_candidates(self):
        today = datetime.now(timezone.utc).date()
        for i in range(40):
            record = {
                "question": f"Question {i} about scaling distributed databases",
                "topic": "databases/scaling",
                "researched_on": today.isoformat(),
                "freshness": "stable",
                "sources": [{"id": "s1", "url": "https://example.com/db"}],
                "findings": [{"claim": f"Claim {i} database partitioning", "class": "fact", "source_ids": ["s1"]}]
            }
            research_ledger.save_record(record)

        res = research_ledger.lookup_record("scaling distributed databases")
        self.assertLessEqual(len(res["records"]), 32)


class TestMigration(BaseTempDirTestCase):
    """Tests for section 4 migrate dry-run and --apply."""

    def test_migrate_dry_run_and_apply_and_idempotency(self):
        """Test (f): migrate dry run reports old/new keys and changes nothing; --apply backs up, migrates, keeps lookup working, and second --apply is a no-op."""
        today = datetime.now(timezone.utc).date()
        valid_until = (today + timedelta(days=90)).isoformat()
        now_iso = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
        CREATE TABLE research_records (
            topic_key TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            researched_on TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            freshness TEXT NOT NULL,
            supersedes TEXT,
            body TEXT,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE VIRTUAL TABLE research_fts USING fts5(
            topic_key,
            topic,
            question,
            claims
        )
        """)

        # Old record 1: qualifies as verified
        old_key_1 = "research/databases/sqlite/how-does-sqlite-wal-checkpointing-work"
        q1 = "How does SQLite WAL checkpointing work?"
        t1 = "databases/sqlite"
        data_1 = {
            "kind": "research",
            "topic_key": old_key_1,
            "question": q1,
            "topic": t1,
            "researched_on": today.isoformat(),
            "valid_until": valid_until,
            "freshness": "stable",
            "confidence": "high",
            "sources": [{"id": "s1", "url": "https://sqlite.org/wal.html"}],
            "findings": [{"claim": "PASSIVE, FULL, RESTART and TRUNCATE modes exist", "class": "fact", "source_ids": ["s1"], "as_of": today.isoformat()}],
        }
        conn.execute(
            "INSERT INTO research_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (old_key_1, t1, q1, today.isoformat(), valid_until, "stable", None, "body1", json.dumps(data_1), now_iso, now_iso),
        )
        conn.execute(
            "INSERT INTO research_fts VALUES (?, ?, ?, ?)",
            (old_key_1, t1, q1, "PASSIVE, FULL, RESTART and TRUNCATE modes exist"),
        )

        # Old record 2: written under old lenient rules (class='fact' with no sources), becomes draft with reasons
        old_key_2 = "research/python/runtime/how-does-the-python-gil-affect-threads"
        q2 = "How does the Python GIL affect threads?"
        t2 = "python/runtime"
        data_2 = {
            "kind": "research",
            "topic_key": old_key_2,
            "question": q2,
            "topic": t2,
            "researched_on": today.isoformat(),
            "valid_until": valid_until,
            "freshness": "stable",
            "confidence": "medium",
            "sources": [],
            "findings": [{"claim": "Only one thread executes Python bytecode at once", "class": "fact", "source_ids": [], "as_of": today.isoformat()}],
        }
        conn.execute(
            "INSERT INTO research_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (old_key_2, t2, q2, today.isoformat(), valid_until, "stable", None, "body2", json.dumps(data_2), now_iso, now_iso),
        )
        conn.execute(
            "INSERT INTO research_fts VALUES (?, ?, ?, ?)",
            (old_key_2, t2, q2, "Only one thread executes Python bytecode at once"),
        )
        conn.commit()
        conn.close()

        expected_new_1 = research_ledger.make_topic_key(t1, q1)
        expected_new_2 = research_ledger.make_topic_key(t2, q2)

        # 1. Dry run via CLI
        stdout_dry = io.StringIO()
        with mock.patch("sys.stdout", stdout_dry):
            with mock.patch("sys.argv", ["research_ledger.py", "migrate"]):
                exit_code = research_ledger.main()
                self.assertEqual(exit_code, 0)

        dry_report = json.loads(stdout_dry.getvalue())
        self.assertEqual(dry_report["db_path"], self.db_path)
        self.assertEqual(dry_report["conflicts"], [])
        self.assertEqual(len(dry_report["records"]), 2)
        by_old = {r["old_key"]: r for r in dry_report["records"]}
        self.assertEqual(by_old[old_key_1]["new_key"], expected_new_1)
        self.assertEqual(by_old[old_key_1]["evidence"], "verified")
        self.assertEqual(by_old[old_key_1]["reasons"], [])
        self.assertEqual(by_old[old_key_2]["new_key"], expected_new_2)
        self.assertEqual(by_old[old_key_2]["evidence"], "draft")
        self.assertTrue(len(by_old[old_key_2]["reasons"]) >= 1)

        # Verify dry run changed nothing in DB and created no backup files
        conn = sqlite3.connect(self.db_path)
        keys_in_db = {r[0] for r in conn.execute("SELECT topic_key FROM research_records").fetchall()}
        has_rev_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_revisions'"
        ).fetchone()
        conn.close()
        self.assertEqual(keys_in_db, {old_key_1, old_key_2})
        self.assertIsNone(has_rev_table)
        bak_files = [f for f in os.listdir(self.tmpdir.name) if ".bak-" in f]
        self.assertEqual(bak_files, [])

        # 2. Apply migration via CLI
        stdout_apply = io.StringIO()
        with mock.patch("sys.stdout", stdout_apply):
            with mock.patch("sys.argv", ["research_ledger.py", "migrate", "--apply"]):
                exit_code = research_ledger.main()
                self.assertEqual(exit_code, 0)

        apply_report = json.loads(stdout_apply.getvalue())
        self.assertTrue(apply_report["applied"])
        self.assertIsNotNone(apply_report["backup_path"])
        self.assertTrue(os.path.exists(apply_report["backup_path"]))

        conn = sqlite3.connect(self.db_path)
        new_rows = conn.execute("SELECT topic_key, data_json FROM research_records").fetchall()
        rev_rows = conn.execute("SELECT topic_key, revision, data_json FROM research_revisions").fetchall()
        conn.close()

        self.assertEqual({r[0] for r in new_rows}, {expected_new_1, expected_new_2})
        self.assertEqual(len(rev_rows), 2)
        for tk, dj in new_rows:
            parsed = json.loads(dj)
            self.assertEqual(parsed["topic_key"], tk)
            self.assertEqual(parsed["revision"], 1)
            self.assertEqual(parsed["evidence"], "verified" if tk == expected_new_1 else "draft")

        # Both records must remain findable by lookup_record
        res1 = research_ledger.lookup_record(q1)
        self.assertEqual(res1["status"], "hit_fresh")
        self.assertEqual(res1["records"][0]["topic_key"], expected_new_1)

        res2 = research_ledger.lookup_record(q2)
        self.assertEqual(res2["status"], "partial")  # draft record -> partial
        self.assertEqual(res2["records"][0]["topic_key"], expected_new_2)

        # 3. Second --apply is a no-op (changes nothing, creates no new backup)
        bak_files_after_first = sorted(f for f in os.listdir(self.tmpdir.name) if ".bak-" in f)
        stdout_apply2 = io.StringIO()
        with mock.patch("sys.stdout", stdout_apply2):
            with mock.patch("sys.argv", ["research_ledger.py", "migrate", "--apply"]):
                exit_code = research_ledger.main()
                self.assertEqual(exit_code, 0)

        apply2_report = json.loads(stdout_apply2.getvalue())
        self.assertFalse(apply2_report["applied"])
        self.assertIsNone(apply2_report["backup_path"])
        bak_files_after_second = sorted(f for f in os.listdir(self.tmpdir.name) if ".bak-" in f)
        self.assertEqual(bak_files_after_second, bak_files_after_first)

    def test_migrate_refuses_on_conflicts(self):
        today = datetime.now(timezone.utc).date().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        CREATE TABLE research_records (
            topic_key TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            researched_on TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            freshness TEXT NOT NULL,
            supersedes TEXT,
            body TEXT,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        for idx, old_k in enumerate(("research/t/q-1", "research/t/q-2")):
            d = {"topic": "t", "question": "Identical question?"}
            conn.execute(
                "INSERT INTO research_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (old_k, "t", "Identical question?", today, today, "stable", None, f"b{idx}", json.dumps(d), today, today),
            )
        conn.commit()
        conn.close()

        dry = research_ledger.migrate_db(apply=False)
        self.assertEqual(len(dry["conflicts"]), 1)

        with self.assertRaises(ValueError):
            research_ledger.migrate_db(apply=True)



class TestStats(BaseTempDirTestCase):
    """Tests daily stats tracking in stats.json and stats CLI."""

    def test_stats_tracked_on_lookup(self):
        # 1 miss
        research_ledger.lookup_record("Unseen question")
        stats = research_ledger.get_stats()
        today_str = datetime.now(timezone.utc).date().isoformat()
        self.assertIn(today_str, stats)
        self.assertEqual(stats[today_str]["lookups"], 1)
        self.assertEqual(stats[today_str]["misses"], 1)

        # 1 hit_fresh (must be a verified record)
        today = datetime.now(timezone.utc).date()
        record = {
            "question": "What is Python GIL?",
            "topic": "python/runtime",
            "researched_on": today.isoformat(),
            "freshness": "stable",
            "sources": [{"id": "s1", "url": "https://docs.python.org/3/glossary.html#term-global-interpreter-lock"}],
            "findings": [{"claim": "GIL is a mutex protecting Python objects", "class": "fact", "source_ids": ["s1"]}],
        }
        research_ledger.save_record(record)
        research_ledger.lookup_record("What is Python GIL?")

        stats = research_ledger.get_stats()
        self.assertEqual(stats[today_str]["lookups"], 2)
        self.assertEqual(stats[today_str]["fresh_hits"], 1)

    def test_cli_stats_command(self):
        today_str = datetime.now(timezone.utc).date().isoformat()
        research_ledger.lookup_record("Sample question for stats")

        stdout_capture = io.StringIO()
        with mock.patch("sys.stdout", stdout_capture):
            with mock.patch("sys.argv", ["research_ledger.py", "stats"]):
                exit_code = research_ledger.main()
                self.assertEqual(exit_code, 0)

        out = json.loads(stdout_capture.getvalue())
        self.assertIn(today_str, out)
        self.assertGreaterEqual(out[today_str]["lookups"], 1)


class TestStricterMatching(BaseTempDirTestCase):
    """A topic filter holds in every search path, and a strong match needs every question word."""

    def test_like_fallback_keeps_the_topic_filter(self):
        today = datetime.now(timezone.utc).date().isoformat()
        research_ledger.save_record({
            "question": "zebra migration patterns", "topic": "alpha", "researched_on": today,
            "sources": [{"id": "s1", "url": "https://example.org/a"}],
            "findings": [{"claim": "Zebras migrate seasonally", "class": "fact", "source_ids": ["s1"]}]})
        res = research_ledger.lookup_record("zebra", topic="beta")
        self.assertEqual(res["status"], "miss")
        self.assertEqual(res["records"], [])

    def test_question_words_missing_from_the_record_are_not_a_fresh_hit(self):
        today = datetime.now(timezone.utc).date().isoformat()
        research_ledger.save_record({
            "question": "How to configure PgBouncer pooling?", "topic": "postgres", "researched_on": today,
            "sources": [{"id": "s1", "url": "https://www.pgbouncer.org"}],
            "findings": [{"claim": "PgBouncer pools connections", "class": "fact", "source_ids": ["s1"]}]})
        res = research_ledger.lookup_record("How to configure PgBouncer pooling for Kubernetes sidecars?")
        self.assertNotEqual(res["status"], "hit_fresh")
