"""Offline decoder regression, no hardware dependencies."""
import importlib.util
import struct
import json
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('analyze', Path(__file__).resolve().parents[1] / 'tools/h6cs_ny8_analyze.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
RULES = [(0xff00, 0x3100, 'CALL', 'addr8'), (0xfe00, 0x3200, 'GOTO', 'addr9'), (0xffff, 0, 'NOP', '')]
class StaticBranches(unittest.TestCase):
    def test_manufacturer_carry_fixture(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/h6cs/nyasm-carry.json').read_text())
        rules = a.rules_from_sleigh('')
        for case in fixture['cases']:
            self.assertEqual(a.decode(case['word'], 0, rules)['name'], case['name'])

    def test_short_branches_are_dynamic(self):
        for word in (0x3155, 0x3355):
            decoded = a.decode(word, 0x700, RULES)
            self.assertIsNone(decoded['target'])
            self.assertIn('PCHBUF', decoded['text'])
        _, _, _, report = a.analyze(struct.pack('<9H', 0x3155, 0x3355, 0, 0, 0, 0, 0, 0, 0), RULES)
        self.assertEqual(report['direct_branches'], [])
        self.assertEqual(report['unresolved_dynamic_branches'], [0, 1])
if __name__ == '__main__':
    unittest.main()
