"""Privacy-safe Jev suggestions for ambiguous local intake artifacts.

The storage engine supplies its Store, typed Jev caller and job updater. This
module never sends a path, filename, job ID or file content to Jev. A suggestion
is data for review, not permission to delete or archive a source.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import time

POLICY = 'storage-classification-v1'
MODEL = 'jev-1.13.0'
BATCH_LIMIT = 8
RETRY_SECONDS = 3600
KNOWN_DURABLE = frozenset({'.txt', '.md', '.pdf', '.png', '.jpg', '.jpeg', '.webp',
                           '.gif', '.mp4', '.mov', '.mp3', '.wav', '.csv', '.json'})
LOCALLY_UNSAFE = frozenset({'.db', '.sqlite', '.sqlite3', '.app', '.crdownload',
                            '.part', '.download', '.tmp'})
DESCRIPTORS = {
    'archive': ('An opaque compressed package in a file intake queue. It could be a '
                'durable delivery or a replaceable download. No name, contents or provenance are supplied.'),
    'installer': ('An opaque software installer package in a file intake queue. It may be '
                  'replaceable. No name, contents or provenance are supplied.'),
    'unknown': ('An opaque standalone regular file of unrecognized type in a file intake '
                'queue. No name, contents or provenance are supplied.'),
}
REASONS = {
    'durable': 'Jev proposed durable material; owner review is required before archive classification.',
    'reproducible': 'Jev proposed replaceable material; no deletion or backup is authorized.',
    'review': 'Jev could not classify this abstract artifact with enough evidence.',
}


def backoff(store, candidates, summary):
    until = time.time() + RETRY_SECONDS
    for row, _, fp in candidates:
        store.set('storage_classify_backoff_' + row['id'], {'fingerprint': fp, 'until': until})
    store.set('jev_last_status', summary['provider_status'])
    store.set('storage_jev_last_usage', summary['usage'])
    return summary


def fingerprint(row, config):
    material = [row['id'], row['dev'], row['ino'], row['size'], row['mtime_ns'],
                POLICY, config.get('jev', {}).get('model', MODEL),
                bool(config.get('automatic_archive')), str(config.get('intake_dir'))]
    return hashlib.sha256(json.dumps(material, separators=(',', ':')).encode()).hexdigest()


OWNER_KEY = 'storage_owner_class_'
OWNER_CATEGORIES = ('ordinary', 'critical')
IDENTITY = ('dev', 'ino', 'size', 'mtime_ns')


def record_owner_class(store, row, category):
    """Remember an explicit owner classification for this exact file.

    The record is bound to the file identity the owner classified. A replaced or
    edited file no longer matches it and falls back to the normal review hold.
    Any other category clears the record.
    """
    if category in OWNER_CATEGORIES:
        store.set(OWNER_KEY + row['id'], {'category': category, 'at': time.time(),
                                          **{key: row[key] for key in IDENTITY}})
    else:
        store.set(OWNER_KEY + row['id'], None)


def owner_classified(store, row):
    """True when the owner classified this unchanged file into its current archive category."""
    record = store.get(OWNER_KEY + row['id'])
    return (isinstance(record, dict) and record.get('category') in OWNER_CATEGORIES and
            record.get('category') == row['category'] and
            all(record.get(key) == row[key] for key in IDENTITY))


def local_kind(row, intake):
    """Return only a closed technical type; never return a source-derived string."""
    path = Path(row['path'])
    intake_path = Path(intake)
    if (path.parent != intake_path or intake_path.is_symlink() or
            not intake_path.is_dir() or path.is_symlink()):
        return None
    try:
        value = path.lstat()
    except OSError:
        return None
    if (not stat.S_ISREG(value.st_mode) or value.st_nlink != 1 or
            (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns) !=
            (row['dev'], row['ino'], row['size'], row['mtime_ns'])):
        return None
    suffix = path.suffix.casefold()
    if suffix in KNOWN_DURABLE or suffix in LOCALLY_UNSAFE:
        return None
    if suffix == '.zip':
        return 'archive'
    if suffix in {'.dmg', '.pkg'}:
        return 'installer'
    return 'unknown'


def classify_pending(config, store, jev_call, job_update):
    """Classify at most eight ambiguous files; return IDs to hold this tick."""
    summary = {'considered': 0, 'suggested': 0, 'review': 0, 'skipped': 0,
               'provider_status': 'not_needed', 'hold_ids': [], 'usage': None}
    if store.get('paused', False) or not config.get('intake_dir'):
        summary['provider_status'] = 'paused' if store.get('paused', False) else 'no_intake'
        return summary
    rows = store.db.execute(
        "SELECT * FROM jobs WHERE state IN ('review','settling') AND category IN ('review','ordinary') "
        "ORDER BY observed_at,id").fetchall()
    candidates = []
    for row in rows:
        kind = local_kind(row, config['intake_dir'])
        if not kind:
            summary['skipped'] += 1
            continue
        # An explicit owner classification of this unchanged file is final;
        # Jev only advises on files nobody has decided about yet.
        if owner_classified(store, row):
            summary['skipped'] += 1
            continue
        # The engine's default ordinary class covers unknown extensions. Hold
        # them in review before provider work so a crash or failed call cannot
        # let a later tick archive them as known durable files.
        if row['category'] == 'ordinary' and row['state'] == 'settling':
            job_update(store, row['id'], category='review', state='review')
        summary['hold_ids'].append(row['id'])
        fp = fingerprint(row, config)
        suggestion = store.get('storage_suggestion_' + row['id'])
        if isinstance(suggestion, dict) and suggestion.get('fingerprint') == fp:
            summary['suggested'] += 1
            continue
        if suggestion is not None:
            store.set('storage_suggestion_' + row['id'], None)
        retry = store.get('storage_classify_backoff_' + row['id'])
        if isinstance(retry, dict) and retry.get('fingerprint') == fp and retry.get('until', 0) > time.time():
            summary['skipped'] += 1
            continue
        if len(candidates) < BATCH_LIMIT:
            candidates.append((row, kind, fp))
    summary['considered'] = len(candidates)
    if not candidates:
        return summary
    if not config.get('jev', {}).get('enabled'):
        summary['provider_status'] = 'disabled'
        return summary
    records = [{'id': 'r' + str(index), 'text': DESCRIPTORS[kind]}
               for index, (_, kind, _) in enumerate(candidates)]
    try:
        response = jev_call(config, store, 'synthetic', {'records': records})
    except Exception:
        response = {'status': 'unavailable'}
    summary['provider_status'] = response.get('status', 'unavailable') if isinstance(response, dict) else 'unavailable'
    summary['usage'] = response.get('usage') if isinstance(response, dict) else None
    if summary['provider_status'] not in ('computed', 'cached') or not isinstance(response.get('result'), dict):
        return backoff(store, candidates, summary)
    result = response['result']
    buckets = result.get('buckets')
    if not isinstance(buckets, dict):
        summary['provider_status'] = 'invalid_result'
        return backoff(store, candidates, summary)
    choices = {}
    for label in ('durable', 'reproducible', 'review', 'none'):
        items = buckets.get(label, [])
        if not isinstance(items, list):
            summary['provider_status'] = 'invalid_result'
            return backoff(store, candidates, summary)
        for item in items:
            if isinstance(item, dict) and isinstance(item.get('id'), str):
                choices.setdefault(item['id'], []).append(label)
    valid_ids = {'r' + str(index) for index in range(len(candidates))}
    if set(choices) - valid_ids:
        summary['provider_status'] = 'invalid_result'
        return backoff(store, candidates, summary)
    weak = result.get('review', [])
    if not isinstance(weak, list):
        summary['provider_status'] = 'invalid_result'
        return backoff(store, candidates, summary)
    weak_ids = {item.get('record', {}).get('id') for item in weak
                if isinstance(item, dict) and isinstance(item.get('record'), dict)}
    now = time.time()
    for index, (row, kind, fp) in enumerate(candidates):
        labels = choices.get('r' + str(index), [])
        proposed = (labels[0] if len(labels) == 1 and labels[0] in REASONS and
                    'r' + str(index) not in weak_ids else 'review')
        record = {'class': 'ordinary' if proposed == 'durable' else
                  'replaceable' if proposed == 'reproducible' else 'review',
                  'reason': REASONS[proposed], 'source': 'jev',
                  'fingerprint': fp, 'policy': POLICY,
                  'model': config.get('jev', {}).get('model', MODEL),
                  'technical_kind': kind, 'at': now,
                  'requires_owner_review': True}
        store.set('storage_suggestion_' + row['id'], record)
        summary['suggested'] += 1
        if proposed == 'review':
            summary['review'] += 1
    store.set('storage_jev_last_usage', summary['usage'])
    return summary
