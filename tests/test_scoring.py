#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Behaviour contracts for the probe.

These are the contracts that v1 broke and that reviewers should be able to
re-run in seconds:

  * the score must SEPARATE an AI-flavoured draft from a human field-notes
    draft (v1 gave both 2.0/4 — see the fixture pair for the counterexample);
  * a signal that cannot be computed honestly must be dropped and its weight
    redistributed, not silently scored as zero;
  * a bad input must exit with an actionable message, never a raw traceback.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'scripts', 'turnitin_sim.py')
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures')


def load_module():
    spec = importlib.util.spec_from_file_location('turnitin_sim', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load_module()


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as fh:
        return fh.read()


def run_cli(*args):
    return subprocess.run([sys.executable, SCRIPT, *args],
                          capture_output=True, text=True)


class TestSeparation(unittest.TestCase):
    """The core contract: a blatant AI draft and a human draft must not tie."""

    MIN_GAP = 40

    def _pair(self, lang):
        ai = probe.analyse(fixture(f'ai_sample_{lang}.txt'), 'ai')
        human = probe.analyse(fixture(f'human_sample_{lang}.txt'), 'human')
        return ai, human

    def test_arabic_pair_separates_and_lands_in_opposite_bands(self):
        ai, human = self._pair('ar')
        self.assertGreaterEqual(ai['ai_likeness'] - human['ai_likeness'], self.MIN_GAP,
                                f"arabic pair did not separate: {ai['ai_likeness']} vs "
                                f"{human['ai_likeness']}")
        self.assertEqual(ai['verdict'], 'AI-leaning')
        self.assertEqual(human['verdict'], 'human-leaning')

    def test_english_pair_separates_and_lands_in_opposite_bands(self):
        ai, human = self._pair('en')
        self.assertGreaterEqual(ai['ai_likeness'] - human['ai_likeness'], self.MIN_GAP,
                                f"english pair did not separate: {ai['ai_likeness']} vs "
                                f"{human['ai_likeness']}")
        self.assertEqual(ai['verdict'], 'AI-leaning')
        self.assertEqual(human['verdict'], 'human-leaning')

    def test_ai_fixture_scores_high_because_of_markers_not_burstiness(self):
        """Pins the weighting fix: markers alone must be enough to flag a draft."""
        ai, human = self._pair('ar')
        self.assertGreater(ai['signals']['ai_patterns']['value'], 0.9)
        self.assertEqual(human['signals']['ai_patterns']['value'], 0.0)


class TestHonestDegradation(unittest.TestCase):
    def test_short_text_is_flagged_as_unreliable(self):
        report = probe.analyse('جملة واحدة فقط هنا.', 'tiny')
        self.assertTrue(any('words' in w for w in report['warnings']),
                        f"no length warning in {report['warnings']}")

    def test_burstiness_dropped_when_too_few_sentences_and_weight_redistributed(self):
        report = probe.analyse('هذا نص قصير جدا. وفيه جملتان فقط.', 'tiny')
        self.assertFalse(report['signals']['burstiness']['valid'])
        self.assertNotIn('burstiness', report['weights_used'])
        self.assertIn('ai_patterns', report['weights_used'])

    def test_lexical_is_reported_but_never_scored(self):
        report = probe.analyse(fixture('human_sample_ar.txt'), 'human')
        self.assertIn('ttr', report['lexical'])
        self.assertNotIn('lexical', report['weights_used'])


class TestInputHandling(unittest.TestCase):
    def test_unsupported_extension_gives_actionable_error(self):
        path = os.path.join(FIXTURES, 'unsupported.bin')
        with open(path, 'wb') as fh:
            fh.write(b'\x00\x01')
        try:
            with self.assertRaises(ValueError) as ctx:
                probe.read_text(path)
            self.assertIn('Unsupported file type', str(ctx.exception))
            self.assertIn('.txt', str(ctx.exception))
        finally:
            os.remove(path)

    def test_missing_file_gives_actionable_error(self):
        with self.assertRaises(ValueError) as ctx:
            probe.read_text(os.path.join(FIXTURES, 'nope.docx'))
        self.assertIn('File not found', str(ctx.exception))

    def test_cli_reads_plain_text(self):
        result = run_cli(os.path.join(FIXTURES, 'ai_sample_ar.txt'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('AI-likeness estimate', result.stdout)

    def test_cli_bad_input_exits_two_without_traceback(self):
        """v1 raised a raw PackageNotFoundError on a .txt path."""
        result = run_cli(os.path.join(FIXTURES, 'missing.txt'))
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertIn('error:', result.stderr)

    def test_cli_json_is_machine_readable(self):
        result = run_cli(os.path.join(FIXTURES, 'human_sample_en.txt'), '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn('ai_likeness', payload)
        self.assertEqual(payload['language'], 'en')

    def test_cli_without_argument_runs_the_demo(self):
        result = run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('embedded demo', result.stdout)


class TestRender(unittest.TestCase):
    def test_render_is_plain_text_and_mentions_the_verdict(self):
        report = probe.analyse(fixture('ai_sample_en.txt'), 'demo')
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            text = probe.render(report)
        self.assertIn(report['verdict'], text)
        self.assertNotIn('Traceback', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
