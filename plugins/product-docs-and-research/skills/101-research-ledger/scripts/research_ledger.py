#!/usr/bin/env python3
"""Research ledger CLI and library.

Stores research records in a local SQLite FTS5 database at a path configured by
the RESEARCH_LEDGER_DB environment variable or ~/.research-ledger/ledger.db.
Tracks daily lookup counters at RESEARCH_LEDGER_STATS or ~/.research-ledger/stats.json.

Commands:
  save --json FILE          Validate record, compute valid_until from freshness class, write it
  lookup "<question>" [--topic T] [--revalidate]
                            FTS ranking over question, topic, and claims (max 32 candidates),
                            returning JSON {"status": "hit_fresh"|"hit_stale"|"partial"|"miss", "records": [...]}
  stats                     Print daily lookup counters
  migrate [--apply]         Inspect or migrate an existing ledger database to hashed keys and revisions
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import unicodedata

FRESHNESS_TTL_DAYS = {
    'volatile': 14,
    'moderate': 28,
    'stable': 90,
}

VALID_FRESHNESS = set(FRESHNESS_TTL_DAYS.keys())
VALID_CLASSES = {'fact', 'vendor', 'community', 'inference'}
VALID_CONFIDENCE = {'high', 'medium', 'low'}
VALID_EVIDENCE = {'verified', 'draft'}

_CURRENT_KEYWORDS_PATTERN = re.compile(
    r'(?<!\w)(?:'
    r'today|current|latest|now|price|prices|pricing|cost|costs|policy|'
    r'bugun|bugün|guncel|güncel|fiyat|fiyatı|fiyatlar|'
    r'son\s+sürüm|son\s+surum'
    r')(?!\w)',
    re.IGNORECASE,
)



def get_db_path() -> str:
    path = os.environ.get('RESEARCH_LEDGER_DB')
    if path:
        return os.path.abspath(os.path.expanduser(path))
    return os.path.expanduser('~/.research-ledger/ledger.db')


def get_stats_path() -> str:
    path = os.environ.get('RESEARCH_LEDGER_STATS')
    if path:
        return os.path.abspath(os.path.expanduser(path))
    return os.path.expanduser('~/.research-ledger/stats.json')


def normalize(text: str) -> str:
    """Normalize text: NFKC, casefold, collapse all whitespace to one space, strip."""
    nfkc = unicodedata.normalize('NFKC', str(text))
    folded = nfkc.casefold()
    return re.sub(r'\s+', ' ', folded).strip()


def slugify(text: str, limit: int = 60) -> str:
    nfkc = unicodedata.normalize('NFKC', str(text))
    folded = nfkc.translate(str.maketrans({'ı': 'i', 'İ': 'I', 'ß': 'ss'}))
    ascii_text = unicodedata.normalize('NFKD', folded).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')[:limit].strip('-')
    return slug or hashlib.sha256(normalize(text).encode('utf-8')).hexdigest()[:8]


def make_topic_key(topic: str, question: str) -> str:
    norm_topic = normalize(topic)
    norm_question = normalize(question)
    topic_parts = [slugify(p, limit=60) for p in topic.split('/') if p.strip()]
    topic_slug = '/'.join(topic_parts) if topic_parts else slugify(topic, limit=60)
    q_slug = slugify(question, limit=60)
    h12 = hashlib.sha256(f"{norm_topic}\n{norm_question}".encode('utf-8')).hexdigest()[:12]
    return f"research/{topic_slug}/{q_slug}--{h12}"


def _parse_iso_date_strict(value: object, field_name: str, today_utc: date) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {field_name}: must be a non-empty ISO date or datetime string, got {value!r}")
    raw = value.strip()
    if raw.endswith(('Z', 'z')):
        raw = raw[:-1] + '+00:00'
    try:
        if len(raw) == 10:
            parsed_date = date.fromisoformat(raw)
        else:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc)
            parsed_date = dt.date()
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}: {value!r} is not a valid ISO date or datetime") from exc

    if parsed_date > today_utc + timedelta(days=1):
        raise ValueError(
            f"Invalid {field_name}: {parsed_date.isoformat()} is later than today UTC + 1 day "
            f"({(today_utc + timedelta(days=1)).isoformat()})"
        )
    return parsed_date


def validate_and_normalize_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("Record must be a JSON object")

    kind = record.get('kind', 'research')
    if kind is None:
        kind = 'research'
    if kind != 'research':
        raise ValueError(f"Invalid kind: expected 'research', got {kind!r}")

    question = record.get('question')
    if not question or not isinstance(question, str) or not question.strip():
        raise ValueError("Record 'question' is required and must be a non-empty string")
    question = question.strip()

    topic = record.get('topic')
    if not topic or not isinstance(topic, str) or not topic.strip():
        raise ValueError("Record 'topic' is required and must be a non-empty string")
    topic = topic.strip()

    today_utc = datetime.now(timezone.utc).date()
    if 'researched_on' not in record or record['researched_on'] is None:
        r_date = today_utc
    else:
        r_date = _parse_iso_date_strict(record['researched_on'], 'researched_on', today_utc)
    researched_on_str = r_date.isoformat()

    if 'freshness' not in record or record['freshness'] is None:
        freshness = 'moderate'
    else:
        freshness = record['freshness']
        if not isinstance(freshness, str) or freshness not in VALID_FRESHNESS:
            raise ValueError(f"Invalid freshness: expected one of {sorted(VALID_FRESHNESS)}, got {freshness!r}")

    if 'confidence' not in record or record['confidence'] is None:
        confidence = 'medium'
    else:
        confidence = record['confidence']
        if not isinstance(confidence, str) or confidence not in VALID_CONFIDENCE:
            raise ValueError(f"Invalid confidence: expected one of {sorted(VALID_CONFIDENCE)}, got {confidence!r}")

    # Date arithmetic computed in code
    ttl = FRESHNESS_TTL_DAYS[freshness]
    valid_until_date = r_date + timedelta(days=ttl)
    valid_until_str = valid_until_date.isoformat()

    projects = record.get('projects')
    if not isinstance(projects, list):
        projects = [projects] if projects else []

    plan_items = record.get('plan_items')
    if not isinstance(plan_items, list):
        plan_items = [plan_items] if plan_items else []

    client = record.get('client', 'python')
    if client is None:
        client = 'python'

    if 'sources' not in record or record['sources'] is None:
        sources_raw = []
    else:
        sources_raw = record['sources']
        if not isinstance(sources_raw, list):
            raise ValueError("Record 'sources' must be a list")

    sources = []
    seen_source_ids: set[str] = set()
    for s in sources_raw:
        if not isinstance(s, dict):
            raise ValueError("Each source in 'sources' must be an object")
        sid = s.get('id')
        if not isinstance(sid, str) or not sid.strip():
            raise ValueError("Each source must have a non-empty string 'id'")
        sid = sid.strip()
        if sid in seen_source_ids:
            raise ValueError(f"Duplicate source id: {sid!r}")
        seen_source_ids.add(sid)
        s_copy = dict(s)
        s_copy['id'] = sid
        sources.append(s_copy)

    if 'findings' not in record or record['findings'] is None:
        findings_raw = []
    else:
        findings_raw = record['findings']
        if not isinstance(findings_raw, list):
            raise ValueError("Record 'findings' must be a list")

    findings = []
    for f in findings_raw:
        if not isinstance(f, dict):
            raise ValueError("Each finding in 'findings' must be an object")
        claim = f.get('claim')
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("Each finding must have a non-empty string 'claim'")
        claim = claim.strip()

        if 'class' not in f or f['class'] is None:
            f_class = 'inference'
        else:
            f_class = f['class']
            if not isinstance(f_class, str) or f_class not in VALID_CLASSES:
                raise ValueError(f"Invalid finding class: expected one of {sorted(VALID_CLASSES)}, got {f_class!r}")

        if 'source_ids' not in f or f['source_ids'] is None:
            raw_source_ids = []
        else:
            raw_source_ids = f['source_ids']
            if not isinstance(raw_source_ids, list):
                raise ValueError("Finding 'source_ids' must be a list")

        source_ids = []
        for sid in raw_source_ids:
            if not isinstance(sid, str) or not sid.strip():
                raise ValueError(f"Finding 'source_ids' entries must be non-empty strings, got {sid!r}")
            sid_clean = sid.strip()
            if sid_clean not in seen_source_ids:
                raise ValueError(f"Unknown source_id {sid_clean!r} not present in 'sources'")
            source_ids.append(sid_clean)

        if f_class == 'fact' and not source_ids:
            raise ValueError("A finding of class 'fact' requires at least one source_id")

        if 'as_of' not in f or f['as_of'] is None:
            as_of_str = researched_on_str
        else:
            as_of_date = _parse_iso_date_strict(f['as_of'], "finding 'as_of'", today_utc)
            as_of_str = as_of_date.isoformat()

        findings.append({
            'claim': claim,
            'class': f_class,
            'source_ids': source_ids,
            'as_of': as_of_str,
        })

    qualifies_verified = (
        len(findings) >= 1
        and len(sources) >= 1
        and all(len(f['source_ids']) >= 1 for f in findings)
    )
    computed_evidence = 'verified' if qualifies_verified else 'draft'

    if 'evidence' in record and record['evidence'] is not None:
        input_evidence = record['evidence']
        if not isinstance(input_evidence, str) or input_evidence not in VALID_EVIDENCE:
            raise ValueError(f"Invalid evidence: expected one of {sorted(VALID_EVIDENCE)}, got {input_evidence!r}")
        if input_evidence == 'verified' and computed_evidence != 'verified':
            raise ValueError(
                "Record specifies evidence='verified' but does not qualify "
                "(requires at least one finding, at least one source, and every finding citing at least one source)"
            )

    contradictions = record.get('contradictions', [])
    if not isinstance(contradictions, list):
        contradictions = [str(contradictions)] if contradictions else []

    open_questions = record.get('open_questions', [])
    if not isinstance(open_questions, list):
        open_questions = [str(open_questions)] if open_questions else []

    supersedes = record.get('supersedes')
    if supersedes is not None:
        supersedes = str(supersedes).strip()

    raw_rev = record.get('revision')
    revision = raw_rev if isinstance(raw_rev, int) and not isinstance(raw_rev, bool) and raw_rev >= 1 else 1

    norm = {
        'kind': 'research',
        'question': question,
        'topic': topic,
        'researched_on': researched_on_str,
        'valid_until': valid_until_str,
        'freshness': freshness,
        'projects': [str(p) for p in projects],
        'plan_items': [str(pi) for pi in plan_items],
        'client': str(client),
        'findings': findings,
        'sources': sources,
        'contradictions': [str(c) for c in contradictions],
        'open_questions': [str(oq) for oq in open_questions],
        'supersedes': supersedes,
        'confidence': confidence,
        'evidence': computed_evidence,
        'revision': revision,
    }
    return norm


def format_note_body(record: dict) -> str:
    json_block = json.dumps(record, indent=1, ensure_ascii=False)
    lines = [
        "```json",
        json_block,
        "```",
        "",
        f"# Research: {record['question']}",
        f"**Topic**: `{record['topic']}` | **Freshness**: `{record['freshness']}` (Valid until: {record['valid_until']}) | **Confidence**: {record['confidence']}",
    ]
    if record.get('supersedes'):
        lines.append(f"**Supersedes**: `{record['supersedes']}`")
    if record.get('projects'):
        lines.append(f"**Projects**: {', '.join(record['projects'])}")
    if record.get('findings'):
        lines.append("\n## Findings")
        for f in record['findings']:
            c_type = f.get('class', 'inference')
            claim = f.get('claim', '')
            sources = f" (sources: {', '.join(f.get('source_ids', []))})" if f.get('source_ids') else ""
            lines.append(f"- **[{c_type}]** {claim}{sources}")
    if record.get('sources'):
        lines.append("\n## Sources")
        for s in record['sources']:
            sid = s.get('id', '')
            title = s.get('title') or s.get('url') or sid
            url = s.get('url', '')
            if url:
                lines.append(f"- `[{sid}]` [{title}]({url})")
            else:
                lines.append(f"- `[{sid}]` {title}")
    if record.get('contradictions'):
        lines.append("\n## Contradictions")
        for c in record['contradictions']:
            lines.append(f"- {c}")
    if record.get('open_questions'):
        lines.append("\n## Open Questions")
        for oq in record['open_questions']:
            lines.append(f"- {oq}")
    return "\n".join(lines)


def init_sqlite_db(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS research_records (
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
    CREATE VIRTUAL TABLE IF NOT EXISTS research_fts USING fts5(
        topic_key,
        topic,
        question,
        claims
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS research_revisions (
        topic_key TEXT,
        revision INTEGER,
        data_json TEXT,
        saved_at TEXT,
        PRIMARY KEY(topic_key, revision)
    )
    """)
    conn.commit()
    return conn


def save_sqlite(record: dict, body: str, db_path: str) -> str:
    conn = init_sqlite_db(db_path)
    topic_key = record.get('topic_key') or make_topic_key(record['topic'], record['question'])
    record['topic_key'] = topic_key
    now_iso = datetime.now(timezone.utc).isoformat()
    claims_text = " ".join(f.get("claim", "") for f in record.get("findings", []) if isinstance(f, dict))

    with conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(revision), 0) FROM research_revisions WHERE topic_key = ?",
            (topic_key,),
        ).fetchone()
        next_revision = (int(row[0]) if row and row[0] is not None else 0) + 1
        record['revision'] = next_revision
        data_json = json.dumps(record, ensure_ascii=False)
        body = format_note_body(record)

        conn.execute("""
        INSERT INTO research_records (
            topic_key, topic, question, researched_on, valid_until, freshness,
            supersedes, body, data_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(topic_key) DO UPDATE SET
            topic=excluded.topic,
            question=excluded.question,
            researched_on=excluded.researched_on,
            valid_until=excluded.valid_until,
            freshness=excluded.freshness,
            supersedes=excluded.supersedes,
            body=excluded.body,
            data_json=excluded.data_json,
            updated_at=excluded.updated_at
        """, (
            topic_key, record['topic'], record['question'], record['researched_on'],
            record['valid_until'], record['freshness'], record.get('supersedes'),
            body, data_json, now_iso, now_iso
        ))
        conn.execute(
            "INSERT INTO research_revisions (topic_key, revision, data_json, saved_at) VALUES (?, ?, ?, ?)",
            (topic_key, next_revision, data_json, now_iso),
        )
        conn.execute("DELETE FROM research_fts WHERE topic_key = ?", (topic_key,))
        conn.execute(
            "INSERT INTO research_fts (topic_key, topic, question, claims) VALUES (?, ?, ?, ?)",
            (topic_key, record['topic'], record['question'], claims_text)
        )
    conn.close()
    return topic_key


def search_sqlite(query: str, topic: str | None, db_path: str, limit: int = 32) -> list[dict]:
    if not os.path.exists(db_path):
        return []
    conn = init_sqlite_db(db_path)
    words = re.findall(r'[\w]+', query)
    records = []

    if words:
        fts_tokens = [f'"{w}"' for w in words if len(w) > 1 or w.isalnum()]
        fts_match = " OR ".join(fts_tokens)
        try:
            if topic:
                sql = """
                SELECT r.data_json
                FROM research_fts f
                JOIN research_records r ON f.topic_key = r.topic_key
                WHERE research_fts MATCH ? AND (r.topic = ? OR r.topic LIKE ?)
                ORDER BY f.rank ASC
                LIMIT ?
                """
                params = (fts_match, topic, f"%{topic}%", limit)
            else:
                sql = """
                SELECT r.data_json
                FROM research_fts f
                JOIN research_records r ON f.topic_key = r.topic_key
                WHERE research_fts MATCH ?
                ORDER BY f.rank ASC
                LIMIT ?
                """
                params = (fts_match, limit)
            rows = conn.execute(sql, params).fetchall()
            for (dj,) in rows:
                try:
                    records.append(json.loads(dj))
                except Exception:
                    pass
        except sqlite3.OperationalError:
            pass

    if not records and topic:
        rows = conn.execute(
            "SELECT data_json FROM research_records WHERE topic = ? OR topic LIKE ? ORDER BY researched_on DESC LIMIT ?",
            (topic, f"%{topic}%", limit)
        ).fetchall()
        for (dj,) in rows:
            try:
                records.append(json.loads(dj))
            except Exception:
                pass

    if not records and words:
        like_clauses = ["question LIKE ?" for _ in words[:4]]
        params: list = [f"%{w}%" for w in words[:4]]
        where_sql = f"({' OR '.join(like_clauses)})"
        if topic:
            where_sql += " AND (topic = ? OR topic LIKE ?)"
            params.extend([topic, f"%{topic}%"])
        sql = f"SELECT data_json FROM research_records WHERE {where_sql} ORDER BY researched_on DESC LIMIT ?"
        params.append(limit)
        try:
            rows = conn.execute(sql, params).fetchall()
            for (dj,) in rows:
                try:
                    records.append(json.loads(dj))
                except Exception:
                    pass
        except Exception:
            pass

    conn.close()
    return records[:limit]


def save_record(raw_record: dict) -> dict:
    record = validate_and_normalize_record(raw_record)
    topic_key = make_topic_key(record['topic'], record['question'])
    record['topic_key'] = topic_key
    body = format_note_body(record)
    db_path = get_db_path()

    save_sqlite(record, body, db_path)

    return {
        "status": "ok",
        "topic_key": topic_key,
        "valid_until": record['valid_until'],
        "freshness": record['freshness'],
        "evidence": record['evidence'],
        "revision": record['revision'],
        "record": record
    }


def record_lookup_stats(status: str, stats_file_path: str) -> None:
    today_str = datetime.now(timezone.utc).date().isoformat()
    os.makedirs(os.path.dirname(stats_file_path), exist_ok=True)

    stats_data = {}
    if os.path.exists(stats_file_path):
        try:
            with open(stats_file_path, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
        except Exception:
            stats_data = {}

    if today_str not in stats_data or not isinstance(stats_data[today_str], dict):
        stats_data[today_str] = {
            "lookups": 0,
            "fresh_hits": 0,
            "stale_hits": 0,
            "misses": 0,
            "partial_hits": 0
        }

    day_stats = stats_data[today_str]
    day_stats["lookups"] = day_stats.get("lookups", 0) + 1
    if status == "hit_fresh":
        day_stats["fresh_hits"] = day_stats.get("fresh_hits", 0) + 1
    elif status == "hit_stale":
        day_stats["stale_hits"] = day_stats.get("stale_hits", 0) + 1
    elif status == "miss":
        day_stats["misses"] = day_stats.get("misses", 0) + 1
    elif status == "partial":
        day_stats["partial_hits"] = day_stats.get("partial_hits", 0) + 1

    tmp_path = f"{stats_file_path}.tmp.{os.getpid()}"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        os.replace(tmp_path, stats_file_path)
    except Exception as exc:
        sys.stderr.write(f"[research-ledger] Failed to write stats: {exc}\n")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _question_asks_for_current(question: str) -> bool:
    q_nfkc = unicodedata.normalize('NFKC', str(question))
    q_cf = q_nfkc.casefold().replace('\u0307', '')
    q_tr = q_nfkc.translate(str.maketrans({'İ': 'i', 'I': 'ı'})).casefold().replace('\u0307', '')
    return bool(_CURRENT_KEYWORDS_PATTERN.search(q_cf) or _CURRENT_KEYWORDS_PATTERN.search(q_tr))


def lookup_record(question: str, topic: str | None = None, revalidate: bool = False) -> dict:
    db_path = get_db_path()
    records = search_sqlite(question, topic, db_path, limit=32)

    today = datetime.now(timezone.utc).date()
    if not records:
        status = "miss"
    else:
        top = records[0]
        vu_str = top.get('valid_until', '')
        is_fresh = False
        if vu_str:
            try:
                vu_date = datetime.fromisoformat(vu_str).date()
                is_fresh = (vu_date >= today)
            except Exception:
                is_fresh = False

        q_words = set(re.findall(r'[\w]+', question.lower()))
        top_q = top.get('question', '').lower()
        top_q_words = set(re.findall(r'[\w]+', top_q))
        top_topic = top.get('topic', '').lower()
        top_claims = " ".join(f.get('claim', '') for f in top.get('findings', [])).lower()
        top_claim_words = set(re.findall(r'[\w]+', top_claims))

        overlap_q = q_words & top_q_words
        overlap_all = q_words & (top_q_words | top_claim_words)

        exact_q = (re.sub(r'\W+', '', question.lower()) == re.sub(r'\W+', '', top_q))
        overlap_q_ratio = len(overlap_q) / len(q_words) if q_words else 0
        overlap_all_ratio = len(overlap_all) / len(q_words) if q_words else 0

        top_topic_words = set(re.findall(r'[\w]+', top_topic))
        record_words = top_q_words | top_claim_words | top_topic_words
        topic_matches = (not topic) or (topic.lower() == top_topic or topic.lower() in top_topic)

        is_strong_match = topic_matches and (
            exact_q or (
                bool(q_words) and q_words <= record_words and (
                    overlap_q_ratio >= 0.6 or
                    (len(q_words) <= 2 and overlap_q_ratio >= 0.5) or
                    (overlap_all_ratio >= 0.75)
                )
            )
        )

        if is_strong_match:
            status = "hit_fresh" if is_fresh else "hit_stale"
        elif overlap_all_ratio > 0.15 or len(overlap_all) >= 1 or (topic and topic.lower() in top_topic):
            status = "partial"
        else:
            status = "miss"

        if status == "hit_fresh":
            if top.get('evidence') != 'verified':
                status = "partial"
            else:
                researched_on_date = None
                ro_str = top.get('researched_on', '')
                if ro_str:
                    try:
                        researched_on_date = date.fromisoformat(str(ro_str)[:10])
                    except Exception:
                        researched_on_date = None
                if revalidate or (_question_asks_for_current(question) and researched_on_date != today):
                    status = "hit_stale"

    record_lookup_stats(status, get_stats_path())

    return {
        "status": status,
        "records": records if status != "miss" else []
    }


def _evaluate_record_for_migration(data: dict) -> tuple[str, list[str]]:
    """Compute ('verified'|'draft', reasons) for a stored record without rejecting."""
    reasons: list[str] = []
    if not isinstance(data, dict):
        return 'draft', ['Record is not a JSON object']

    today_utc = datetime.now(timezone.utc).date()

    kind = data.get('kind', 'research')
    if kind is not None and kind != 'research':
        reasons.append(f"Invalid kind: {kind!r}")

    question = data.get('question')
    if not question or not isinstance(question, str) or not question.strip():
        reasons.append("Missing or empty 'question'")

    topic = data.get('topic')
    if not topic or not isinstance(topic, str) or not topic.strip():
        reasons.append("Missing or empty 'topic'")

    if 'researched_on' in data and data['researched_on'] is not None:
        try:
            _parse_iso_date_strict(data['researched_on'], 'researched_on', today_utc)
        except ValueError as exc:
            reasons.append(str(exc))

    if 'freshness' in data and data['freshness'] is not None:
        if not isinstance(data['freshness'], str) or data['freshness'] not in VALID_FRESHNESS:
            reasons.append(f"Invalid freshness: {data['freshness']!r}")

    if 'confidence' in data and data['confidence'] is not None:
        if not isinstance(data['confidence'], str) or data['confidence'] not in VALID_CONFIDENCE:
            reasons.append(f"Invalid confidence: {data['confidence']!r}")

    sources_raw = data.get('sources')
    valid_source_ids: set[str] = set()
    valid_sources_count = 0
    if sources_raw is not None and not isinstance(sources_raw, list):
        reasons.append("Record 'sources' is not a list")
    else:
        for idx, s in enumerate(sources_raw or []):
            if not isinstance(s, dict):
                reasons.append(f"Source[{idx}] is not an object")
                continue
            sid = s.get('id')
            if not isinstance(sid, str) or not sid.strip():
                reasons.append(f"Source[{idx}] is missing a non-empty string 'id'")
                continue
            sid = sid.strip()
            if sid in valid_source_ids:
                reasons.append(f"Duplicate source id: {sid!r}")
                continue
            valid_source_ids.add(sid)
            valid_sources_count += 1

    findings_raw = data.get('findings')
    valid_findings_count = 0
    all_findings_cite_source = True
    if findings_raw is not None and not isinstance(findings_raw, list):
        reasons.append("Record 'findings' is not a list")
    else:
        for idx, f in enumerate(findings_raw or []):
            if not isinstance(f, dict):
                reasons.append(f"Finding[{idx}] is not an object")
                all_findings_cite_source = False
                continue
            claim = f.get('claim')
            if not isinstance(claim, str) or not claim.strip():
                reasons.append(f"Finding[{idx}] is missing a non-empty string 'claim'")
                all_findings_cite_source = False
                continue
            valid_findings_count += 1

            f_class = f.get('class')
            if f_class is None:
                f_class = 'inference'
            elif not isinstance(f_class, str) or f_class not in VALID_CLASSES:
                reasons.append(f"Finding[{idx}] has invalid class: {f_class!r}")

            sids = f.get('source_ids')
            cited_valid = []
            if sids is None:
                sids = []
            if not isinstance(sids, list):
                reasons.append(f"Finding[{idx}] 'source_ids' is not a list")
            else:
                for sid in sids:
                    if not isinstance(sid, str) or not sid.strip():
                        reasons.append(f"Finding[{idx}] has invalid source_id: {sid!r}")
                    elif sid.strip() not in valid_source_ids:
                        reasons.append(f"Finding[{idx}] cites unknown source_id: {sid.strip()!r}")
                    else:
                        cited_valid.append(sid.strip())

            if f_class == 'fact' and not cited_valid:
                reasons.append(f"Finding[{idx}] of class 'fact' has no valid source_id")

            if not cited_valid:
                all_findings_cite_source = False

            if 'as_of' in f and f['as_of'] is not None:
                try:
                    _parse_iso_date_strict(f['as_of'], f"Finding[{idx}] 'as_of'", today_utc)
                except ValueError as exc:
                    reasons.append(str(exc))

    if valid_findings_count == 0:
        reasons.append("Record has no findings")
    if valid_sources_count == 0:
        reasons.append("Record has no sources")
    if valid_findings_count > 0 and not all_findings_cite_source:
        reasons.append("Not every finding cites at least one valid source")

    if not reasons:
        return 'verified', []
    return 'draft', reasons


def migrate_db(apply: bool = False, db_path: str | None = None) -> dict:
    target_db = db_path or get_db_path()
    if not os.path.exists(target_db):
        return {
            "db_path": target_db,
            "database_path": target_db,
            "dry_run": not apply,
            "applied": False,
            "backup_path": None,
            "records": [],
            "conflicts": [],
        }

    conn = sqlite3.connect(target_db)
    try:
        has_records_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_records'"
        ).fetchone() is not None
        has_revisions_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_revisions'"
        ).fetchone() is not None

        rows = []
        if has_records_table:
            rows = conn.execute(
                "SELECT topic_key, topic, question, data_json, created_at FROM research_records ORDER BY rowid ASC"
            ).fetchall()

        existing_revisions: set[str] = set()
        if has_revisions_table:
            rev_rows = conn.execute("SELECT DISTINCT topic_key FROM research_revisions").fetchall()
            existing_revisions = {r[0] for r in rev_rows}
    finally:
        conn.close()

    report_records = []
    by_new_key: dict[str, list[str]] = {}
    parsed_rows = []
    needs_work = False

    for old_key, col_topic, col_question, data_json, created_at in rows:
        try:
            data = json.loads(data_json) if data_json else {}
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

        topic = str(data.get('topic') or col_topic or '').strip()
        question = str(data.get('question') or col_question or '').strip()
        data.setdefault('topic', topic)
        data.setdefault('question', question)

        new_key = make_topic_key(topic, question)
        evidence, reasons = _evaluate_record_for_migration(data)
        by_new_key.setdefault(new_key, []).append(old_key)

        already_migrated_row = (
            old_key == new_key
            and data.get('topic_key') == new_key
            and data.get('evidence') == evidence
            and isinstance(data.get('revision'), int)
            and not isinstance(data.get('revision'), bool)
            and data.get('revision') >= 1
            and new_key in existing_revisions
        )
        if not already_migrated_row:
            needs_work = True

        rec_entry = {
            "old_key": old_key,
            "new_key": new_key,
            "evidence": evidence,
            "reasons": reasons,
        }
        report_records.append(rec_entry)
        parsed_rows.append((old_key, new_key, topic, question, data, evidence, created_at))

    conflicts = [
        {"new_key": nk, "old_keys": oks}
        for nk, oks in by_new_key.items()
        if len(oks) > 1
    ]

    report = {
        "db_path": target_db,
        "database_path": target_db,
        "dry_run": not apply,
        "applied": False,
        "backup_path": None,
        "records": report_records,
        "conflicts": conflicts,
    }

    if not apply:
        return report

    if conflicts:
        raise ValueError(f"Refusing migration due to {len(conflicts)} key conflict(s)")

    if not needs_work:
        return report

    # Checkpoint before copying DB and any -wal/-shm sidecars
    conn = sqlite3.connect(target_db)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error:
        pass
    finally:
        conn.close()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = f"{target_db}.bak-{ts}"
    shutil.copy2(target_db, backup_path)
    for suffix in ("-wal", "-shm"):
        sidecar = f"{target_db}{suffix}"
        if os.path.exists(sidecar):
            shutil.copy2(sidecar, f"{backup_path}{suffix}")

    now_iso = datetime.now(timezone.utc).isoformat()
    conn = init_sqlite_db(target_db)
    try:
        with conn:
            for old_key, new_key, topic, question, data, evidence, created_at in parsed_rows:
                data['topic_key'] = new_key
                data['evidence'] = evidence
                if not isinstance(data.get('revision'), int) or isinstance(data.get('revision'), bool) or data.get('revision', 0) < 1:
                    data['revision'] = 1
                new_data_json = json.dumps(data, ensure_ascii=False)
                try:
                    new_body = format_note_body(data)
                except Exception:
                    new_body = None

                if new_body is not None:
                    conn.execute(
                        "UPDATE research_records SET topic_key = ?, data_json = ?, body = ?, updated_at = ? WHERE topic_key = ?",
                        (new_key, new_data_json, new_body, now_iso, old_key),
                    )
                else:
                    conn.execute(
                        "UPDATE research_records SET topic_key = ?, data_json = ?, updated_at = ? WHERE topic_key = ?",
                        (new_key, new_data_json, now_iso, old_key),
                    )

                cur = conn.execute(
                    "UPDATE research_fts SET topic_key = ? WHERE topic_key = ?",
                    (new_key, old_key),
                )
                if cur.rowcount == 0:
                    fts_exists = conn.execute(
                        "SELECT 1 FROM research_fts WHERE topic_key = ?",
                        (new_key,),
                    ).fetchone()
                    if not fts_exists:
                        claims_text = " ".join(
                            f.get("claim", "") for f in data.get("findings", []) if isinstance(f, dict)
                        )
                        conn.execute(
                            "INSERT INTO research_fts (topic_key, topic, question, claims) VALUES (?, ?, ?, ?)",
                            (new_key, topic, question, claims_text),
                        )

                if old_key != new_key:
                    conn.execute(
                        "UPDATE research_revisions SET topic_key = ? WHERE topic_key = ?",
                        (new_key, old_key),
                    )

                conn.execute(
                    "INSERT OR IGNORE INTO research_revisions (topic_key, revision, data_json, saved_at) VALUES (?, 1, ?, ?)",
                    (new_key, new_data_json, created_at or now_iso),
                )
    finally:
        conn.close()

    report["applied"] = True
    report["backup_path"] = backup_path
    return report


def get_stats() -> dict:
    stats_path = get_stats_path()
    if os.path.exists(stats_path):
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as exc:
            sys.stderr.write(f"[research-ledger] Error reading stats: {exc}\n")
            return {}
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('save', help='Save a validated research record')
    s.add_argument('--json', dest='json_file', help='Path to JSON record file (or - for stdin)')
    s.add_argument('file', nargs='?', help='Positional fallback for record file')

    l = sub.add_parser('lookup', help='Look up existing records for a research question')
    l.add_argument('question', help='Research question')
    l.add_argument('--topic', '-t', default=None, help='Filter by hierarchical topic tag')
    l.add_argument('--revalidate', action='store_true', help='Treat fresh hits as stale to force revalidation')

    sub.add_parser('stats', help='Print daily lookup counters')

    m = sub.add_parser('migrate', help='Inspect or migrate existing database keys and revisions')
    m.add_argument('--apply', action='store_true', help='Write migration changes after backing up the database')

    args = ap.parse_args()

    if args.cmd == 'save':
        target = args.json_file or args.file
        if not target:
            sys.stderr.write("Error: --json FILE is required for save\n")
            return 1
        try:
            if target == '-':
                content = sys.stdin.read()
            else:
                with open(target, 'r', encoding='utf-8') as f:
                    content = f.read()
            data = json.loads(content)
        except Exception as exc:
            sys.stderr.write(f"Error reading JSON from {target}: {exc}\n")
            return 1

        try:
            res = save_record(data)
            json.dump(res, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write('\n')
            return 0
        except Exception as exc:
            sys.stderr.write(f"Error validating/saving record: {exc}\n")
            return 1

    elif args.cmd == 'lookup':
        res = lookup_record(args.question, topic=args.topic, revalidate=args.revalidate)
        json.dump(res, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')
        return 0

    elif args.cmd == 'stats':
        stats_data = get_stats()
        json.dump(stats_data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')
        return 0

    elif args.cmd == 'migrate':
        report = migrate_db(apply=False)
        if args.apply:
            if report['conflicts']:
                json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
                sys.stdout.write('\n')
                sys.stderr.write("Error: refusing migration due to key conflicts\n")
                return 1
            report = migrate_db(apply=True)
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
