"""Wire-level consumer checks; mock transport is not live provider evidence."""
import copy
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from jev.core import MODEL, decide, validate_response, Invalid
from jev.cli import explicit_request
from jev.operations import prepare


def fixtures():
    common = {'task': 'Use the supplied source evidence', 'data_class': 'synthetic',
              'records': [{'id': 'a', 'text': 'Total 120; shipping 5.'}]}
    return [common | {'operation': 'rank'},
            common | {'operation': 'classify', 'labels': {'invoice': 'Invoice amount'}},
            common | {'operation': 'extract', 'fields': {'amount': {
                'description': 'Invoice total', 'candidates': [
                    {'id': 'total', 'record_id': 'a', 'start': 6, 'end': 9}]}}},
            common | {'operation': 'verify', 'claims': [
                {'id': 'total', 'text': 'Total is 120.', 'record_ids': ['a']}]},
            common | {'operation': 'score', 'dimensions': {'detail': {
                'instructions': 'Does the record specify a total?', 'levels': ['Missing', 'Specified']}}},
            common | {'operation': 'route', 'handlers': {'parse': {
                'description': 'Parse amount', 'args': {'format': {
                    'description': 'Output format', 'options': {'json': 'Structured data'}}}}}}]


def wire_response(questions):
    answers = {}
    for key, q in questions.items():
        assert set(q) <= {'type', 'instructions', 'criteria'}
        assert q['instructions']
        if q['type'] == 'noul':
            a = {'type': 'noul', 'noul': 0.01}
        elif q['type'] == 'score':
            top = len(q['criteria']) - 1
            a = {'type': 'score', 'score': top, 'confidence': 0.99,
                 'probabilities': {str(i): int(i == top) for i in range(top + 1)}}
        else:
            chosen = next(iter(q['criteria']))
            a = {'type': 'choice', 'choice': chosen, 'confidence': 0.99,
                 'probabilities': {k: int(k == chosen) for k in q['criteria']}}
        answers[key] = a
    return {'model': MODEL, 'answers': answers, 'usage': {'input_tokens': 90, 'output_tokens': 10}}


class ComputeTests(unittest.TestCase):
    def test_compound_ids_cannot_silently_overwrite_questions(self):
        dimension = {'instructions': 'Evaluate detail', 'levels': ['Missing', 'Present']}
        argument = {'description': 'Output format', 'options': {'json': 'JSON'}}
        cases = [
            {'operation': 'score', 'dimensions': {'c': dimension, 'b:c': dimension}},
            {'operation': 'route', 'handlers': {
                'a:b': {'description': 'First', 'args': {'c': argument}},
                'a': {'description': 'Second', 'args': {'b:c': argument}}}}
        ]
        for case in cases:
            with self.subTest(operation=case['operation']), self.assertRaises(ValueError):
                prepare({'task': 'Process records', 'records': [
                    {'id': 'a:b', 'text': 'First'}, {'id': 'a', 'text': 'Second'}]} | case)

    def test_all_operations_use_real_wire_shape_and_consume_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            config = {'enabled': True, 'public_advice': True, 'projects': {},
                      'monthly_budget_eur': None, 'deadline_seconds': 3,
                      'choice_confidence_floor': 0.4}
            calls = []
            def transport(state, questions, conf, deadline):
                self.assertEqual(state['records'][0]['text'], 'Total 120; shipping 5.')
                self.assertIn('task', state)
                calls.append(questions)
                return {'response': wire_response(questions)}
            results = {}
            for fixture in fixtures():
                request = explicit_request(fixture | {'mode': 'compute'}, 'codex', config)
                result = decide(request, config, {'version': 'test'}, {'version': 'test'},
                                root, root / 'state', transport, explicit_advice=True)
                self.assertEqual(result['status'], 'computed', result)
                self.assertEqual(result['authority'], 'typed_data_only')
                results[fixture['operation']] = result['result']
            self.assertEqual(len(calls), 6)
            self.assertEqual(results['extract']['values']['amount']['value'], '120')
            self.assertEqual(results['classify']['buckets']['invoice'][0]['id'], 'a')
            self.assertEqual(results['route']['call'], {'handler': 'parse', 'arguments': {'format': 'json'}})
            self.assertEqual(results['verify']['claims'][0]['verdict'], 'supported')

    def test_score_response_validation(self):
        _, questions, _ = prepare(fixtures()[0])
        for mutation in ('coverage', 'nan', 'range', 'distribution'):
            response = wire_response(questions)
            answer = next(v for v in response['answers'].values() if v['type'] == 'score')
            if mutation == 'coverage':
                answer['probabilities'] = {'0': 1}
            elif mutation == 'nan':
                answer['score'] = float('nan')
            elif mutation == 'range':
                answer['score'] = 100
            else:
                answer['score'] = 0
            with self.assertRaises(Invalid):
                validate_response(response, questions)

    def test_private_and_sensitive_compute_never_reaches_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            config = {'enabled': True, 'public_advice': True, 'projects': {},
                      'monthly_budget_eur': None, 'deadline_seconds': 3}
            def forbidden(*args):
                self.fail('sensitive data sent')
            for private in (True, False):
                raw = copy.deepcopy(fixtures()[0])
                if private:
                    raw['data_class'] = 'private'
                else:
                    raw['records'][0]['text'] = 'api_key=DO_NOT_TRANSMIT'
                result = decide(explicit_request(raw | {'mode': 'compute'}, 'codex', config),
                    config, {'version': 'test'}, {'version': 'test'}, root, root / 'state',
                    forbidden, explicit_advice=True)
                self.assertEqual(result['api_calls'], 0)
                self.assertEqual(result['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
