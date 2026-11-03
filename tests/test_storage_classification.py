"""Offline intake classification checks; no Jev provider call or real archive."""
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from storage.classification import classify_pending, record_owner_class


class Store:
    def __init__(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.execute('CREATE TABLE jobs (id TEXT,path TEXT,category TEXT,state TEXT,size INTEGER,'
                        'mtime_ns INTEGER,dev INTEGER,ino INTEGER,observed_at INTEGER)')
        self.meta = {}

    def get(self, key, default=None):
        return self.meta.get(key, default)

    def set(self, key, value):
        self.meta[key] = value


def add_file(store, root, name, *, category='review', state='review'):
    path = root / name
    path.write_bytes(b'local bytes that must never reach the provider')
    info = path.stat()
    ident = 'private-job-' + str(store.db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0])
    store.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                     (ident, str(path), category, state, info.st_size, info.st_mtime_ns,
                      info.st_dev, info.st_ino, 1))
    store.db.commit()
    return ident


def update(store, ident, **fields):
    sql = ','.join(key + '=?' for key in fields)
    store.db.execute('UPDATE jobs SET ' + sql + ' WHERE id=?', (*fields.values(), ident))
    store.db.commit()


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.store = Store()
        self.config = {'intake_dir': str(self.root), 'automatic_archive': True,
                       'jev': {'enabled': True}}

    def run_classify(self, provider):
        return classify_pending(self.config, self.store, provider,
                                lambda store, ident, **fields: update(store, ident, **fields))

    def test_payload_has_only_static_abstract_descriptors_and_local_id_mapping(self):
        ident = add_file(self.store, self.root, 'private-client-contract.zip')
        calls = []

        def provider(config, store, data_class, payload):
            calls.append((data_class, payload))
            return {'status': 'computed', 'result': {'buckets': {
                'durable': [{'id': 'r0', 'text': payload['records'][0]['text']}],
                'reproducible': [], 'review': [], 'none': []}, 'review': []}}

        result = self.run_classify(provider)
        self.assertEqual(result['suggested'], 1)
        self.assertEqual(calls[0][0], 'synthetic')
        encoded = json.dumps(calls[0][1])
        for private in (str(self.root), 'private-client-contract', ident, 'local bytes'):
            self.assertNotIn(private, encoded)
        suggestion = self.store.get('storage_suggestion_' + ident)
        self.assertEqual(suggestion['class'], 'ordinary')
        self.assertTrue(suggestion['requires_owner_review'])
        self.assertEqual(self.store.db.execute('SELECT state FROM jobs').fetchone()[0], 'review')

    def test_unknown_ordinary_is_persistently_held_and_failure_backs_off(self):
        ident = add_file(self.store, self.root, 'opaque.custom', category='ordinary', state='settling')
        provider = Mock(return_value={'status': 'unavailable', 'result': None})
        first = self.run_classify(provider)
        self.assertIn(ident, first['hold_ids'])
        self.assertEqual(tuple(self.store.db.execute('SELECT category,state FROM jobs').fetchone()),
                         ('review', 'review'))
        self.assertIsNone(self.store.get('storage_suggestion_' + ident))
        second = self.run_classify(provider)
        self.assertIn(ident, second['hold_ids'])
        self.assertEqual(provider.call_count, 1)

    def test_unchanged_suggestion_cache_avoids_provider_and_changed_file_reasks(self):
        ident = add_file(self.store, self.root, 'opaque.zip')
        provider = Mock(return_value={'status': 'computed', 'result': {'buckets': {
            'reproducible': [{'id': 'r0'}], 'durable': [], 'review': [], 'none': []}}})
        self.run_classify(provider)
        self.run_classify(provider)
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(self.store.get('storage_suggestion_' + ident)['class'], 'replaceable')
        path = self.root / 'opaque.zip'
        path.write_bytes(b'changed local source')
        info = path.stat()
        update(self.store, ident, size=info.st_size, mtime_ns=info.st_mtime_ns,
               dev=info.st_dev, ino=info.st_ino)
        self.run_classify(provider)
        self.assertEqual(provider.call_count, 2)

    def test_provider_error_keeps_review_job_unchanged(self):
        ident = add_file(self.store, self.root, 'delivery.zip')
        before = tuple(self.store.db.execute('SELECT category,state FROM jobs WHERE id=?',
                                             (ident,)).fetchone())
        result = self.run_classify(lambda *_: {'status': 'unavailable', 'result': None})
        after = tuple(self.store.db.execute('SELECT category,state FROM jobs WHERE id=?',
                                            (ident,)).fetchone())
        self.assertEqual(result['provider_status'], 'unavailable')
        self.assertEqual(after, before)
        self.assertIsNone(self.store.get('storage_suggestion_' + ident))

    def row(self, ident):
        return self.store.db.execute('SELECT * FROM jobs WHERE id=?', (ident,)).fetchone()

    def test_owner_classified_unknown_file_is_not_put_back_in_review(self):
        ident = add_file(self.store, self.root, 'delivery.tar', category='ordinary', state='settling')
        record_owner_class(self.store, self.row(ident), 'ordinary')
        provider = Mock()
        result = self.run_classify(provider)
        self.assertNotIn(ident, result['hold_ids'])
        self.assertEqual(tuple(self.store.db.execute('SELECT category,state FROM jobs').fetchone()),
                         ('ordinary', 'settling'))
        provider.assert_not_called()

    def test_owner_class_is_bound_to_file_identity(self):
        ident = add_file(self.store, self.root, 'delivery.tar', category='ordinary', state='settling')
        record_owner_class(self.store, self.row(ident), 'ordinary')
        path = self.root / 'delivery.tar'
        path.write_bytes(b'replaced after the owner decided')
        info = path.stat()
        update(self.store, ident, size=info.st_size, mtime_ns=info.st_mtime_ns,
               dev=info.st_dev, ino=info.st_ino)
        result = self.run_classify(Mock(return_value={'status': 'unavailable', 'result': None}))
        self.assertIn(ident, result['hold_ids'])
        self.assertEqual(tuple(self.store.db.execute('SELECT category,state FROM jobs').fetchone()),
                         ('review', 'review'))

    def test_review_choice_clears_owner_class(self):
        ident = add_file(self.store, self.root, 'delivery.tar', category='ordinary', state='settling')
        record_owner_class(self.store, self.row(ident), 'ordinary')
        record_owner_class(self.store, self.row(ident), 'review')
        result = self.run_classify(Mock(return_value={'status': 'unavailable', 'result': None}))
        self.assertIn(ident, result['hold_ids'])

    def test_paused_and_known_durable_do_not_call_provider(self):
        add_file(self.store, self.root, 'known.pdf', category='ordinary', state='settling')
        provider = Mock()
        self.assertEqual(self.run_classify(provider)['considered'], 0)
        self.store.set('paused', True)
        add_file(self.store, self.root, 'opaque.zip')
        self.assertEqual(self.run_classify(provider)['provider_status'], 'paused')
        provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
