#!/usr/bin/env python3
"""Research ledger CLI and library.

Stores research records in a local SQLite FTS5 database at a path configured by
the RESEARCH_LEDGER_DB environment variable or ~/.research-ledger/ledger.db.
Tracks daily lookup counters at RESEARCH_LEDGER_STATS or ~/.research-ledger/stats.json.

Commands:
  save --json FILE          Validate record, compute valid_until from freshness class, write it
  lookup "<question>" [--topic T]
                            FTS ranking over question, topic, and claims (max 32 candidates),
                            returning JSON {"status": "hit_fresh"|"hit_stale"|"partial"|"miss", "records": [...]}
  stats                     Print daily lookup counters
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
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


def slugify(text: str, limit: int = 60) -> str:
    folded = text.translate(str.maketrans({'ı': 'i', 'İ': 'I', 'ß': 'ss'}))
    ascii_text = unicodedata.normalize('NFKD', folded).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')[:limit].strip('-')
    return slug or hashlib.sha256(text.encode()).hexdigest()[:8]


def make_topic_key(topic: str, question: str) -> str:
    topic_parts = [slugify(p) for p in topic.split('/') if p.strip()]
    topic_slug = '/'.join(topic_parts) if topic_parts else slugify(topic)
    q_slug = slugify(question, limit=60)
    return f"research/{topic_slug}/{q_slug}"


def validate_and_normalize_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("Record must be a JSON object")

    kind = record.get('kind', 'research')
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

    researched_on = record.get('researched_on')
    if researched_on:
        try:
            r_date = datetime.fromisoformat(str(researched_on)).date()
        except ValueError:
            r_date = datetime.now(timezone.utc).date()
    else:
        r_date = datetime.now(timezone.utc).date()
    researched_on_str = r_date.isoformat()

    freshness = record.get('freshness', 'moderate')
    if freshness not in VALID_FRESHNESS:
        freshness = 'moderate'

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

    findings_raw = record.get('findings', [])
    if not isinstance(findings_raw, list):
        findings_raw = []
    findings = []
    for f in findings_raw:
        if isinstance(f, dict):
            claim = str(f.get('claim', '')).strip()
            if not claim:
                continue
            f_class = f.get('class', 'fact')
            if f_class not in VALID_CLASSES:
                f_class = 'fact'
            source_ids = f.get('source_ids', [])
            if not isinstance(source_ids, list):
                source_ids = [str(source_ids)]
            as_of = f.get('as_of', researched_on_str)
            findings.append({
                'claim': claim,
                'class': f_class,
                'source_ids': [str(s) for s in source_ids],
                'as_of': str(as_of)
            })

    sources_raw = record.get('sources', [])
    if not isinstance(sources_raw, list):
        sources_raw = []
    sources = []
    for s in sources_raw:
        if isinstance(s, dict):
            sources.append(s)

    contradictions = record.get('contradictions', [])
    if not isinstance(contradictions, list):
        contradictions = [str(contradictions)] if contradictions else []

    open_questions = record.get('open_questions', [])
    if not isinstance(open_questions, list):
        open_questions = [str(open_questions)] if open_questions else []

    supersedes = record.get('supersedes')
    if supersedes is not None:
        supersedes = str(supersedes).strip()

    confidence = record.get('confidence', 'medium')
    if confidence not in VALID_CONFIDENCE:
        confidence = 'medium'

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
            c_type = f.get('class', 'fact')
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
    conn.commit()
    return conn


def save_sqlite(record: dict, body: str, db_path: str) -> str:
    conn = init_sqlite_db(db_path)
    topic_key = record.get('topic_key') or make_topic_key(record['topic'], record['question'])
    now_iso = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(record, ensure_ascii=False)
    claims_text = " ".join(f.get("claim", "") for f in record.get("findings", []) if isinstance(f, dict))

    with conn:
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


def lookup_record(question: str, topic: str | None = None) -> dict:
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

    record_lookup_stats(status, get_stats_path())

    return {
        "status": status,
        "records": records if status != "miss" else []
    }


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

    sub.add_parser('stats', help='Print daily lookup counters')

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
        res = lookup_record(args.question, topic=args.topic)
        json.dump(res, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')
        return 0

    elif args.cmd == 'stats':
        stats_data = get_stats()
        json.dump(stats_data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
