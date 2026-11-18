"""Python producer boundary checks in isolated processes, preserving FIR oracle isolation."""

import subprocess
import sys
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]


class TestPythonODEProducer(unittest.TestCase):
    def run_probe(self, body):
        script = (
            "import sys\n"
            f"sys.path.insert(0, {str(NATIVE)!r})\n"
            "from unittest.mock import patch\n"
            "import run_ode as producer\n"
            "from ode_common import make_references\n"
            "from common import blob\n"
            "revision = '1' * 40\n"
            "references = make_references(revision)\n" + body
        )
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_corrupted_reference_model_never_reaches_solver(self):
        self.run_probe(
            "references['scenarios'][0]['artifacts']['model'] = blob(b'wrong model')\n"
            "with patch('run_ode.solve_ode') as solver:\n"
            "    try:\n"
            "        producer.produce(references, revision)\n"
            "    except ValueError:\n"
            "        pass\n"
            "    else:\n"
            "        raise AssertionError('corrupt reference accepted')\n"
            "    solver.assert_not_called()\n"
        )

    def test_wrong_native_model_bytes_never_reach_solver(self):
        self.run_probe(
            "original = producer.artifacts\n"
            "def wrong(*args):\n"
            "    result = original(*args)\n"
            "    result['model'] = blob(b'wrong native model')\n"
            "    return result\n"
            "with patch('run_ode.artifacts', side_effect=wrong), patch('run_ode.solve_ode') as solver:\n"
            "    try:\n"
            "        producer.produce(references, revision)\n"
            "    except ValueError as error:\n"
            "        assert 'first differing byte' in str(error), str(error)\n"
            "    else:\n"
            "        raise AssertionError('wrong native bytes accepted')\n"
            "    solver.assert_not_called()\n"
        )

    def test_numerical_failure_retains_diagnostics_without_partial_samples(self):
        self.run_probe(
            "spec = producer.settings(references['studies']['baseline'], (0.0, 1.0), 'DOP853')\n"
            "failure = producer.ODEExecutionError('NONFINITE', spec, 1, 'injected numerical failure')\n"
            "with patch('run_ode.solve_ode', side_effect=failure):\n"
            "    report = producer.produce(references, revision)\n"
            "assert report['runs'] == []\n"
            "assert len(report['failures']) == 1\n"
            "assert report['failures'][0]['category'] == 'NONFINITE'\n"
            "assert report['failures'][0]['nfev'] == 1\n"
        )

    def test_native_source_digests_must_match_canonical_content(self):
        self.run_probe(
            "from types import SimpleNamespace\n"
            "design = producer.DesignDocument.from_json((producer.ROOT / 'spec/fir/proposals/examples/sources/gfp-design.json').read_bytes())\n"
            "experiment = producer.author(design, references['scenarios'][0])\n"
            "compiled = producer.compile_experiment(experiment)\n"
            "for label, source in (('design', design), ('experiment', experiment)):\n"
            "    wrong = SimpleNamespace(digest='0' * 64, canonical_content_bytes=source.canonical_content_bytes)\n"
            "    try:\n"
            "        producer.artifacts(wrong if label == 'design' else design, wrong if label == 'experiment' else experiment, compiled)\n"
            "    except ValueError as error:\n"
            "        assert label + ' digest differs' in str(error), str(error)\n"
            "    else:\n"
            "        raise AssertionError('wrong native source digest accepted')\n"
        )
