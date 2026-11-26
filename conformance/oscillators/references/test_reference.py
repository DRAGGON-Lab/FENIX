"""Controls for candidate analytical definitions, full inputs and exact balances."""

import copy
import hashlib
import json
import tempfile
import unittest
from decimal import Decimal as D
from decimal import localcontext
from pathlib import Path

import reference


class TestAnalyticalReferences(unittest.TestCase):
    def test_all_samples_satisfy_initials_equations_and_precision_refinement(self):
        result = reference.report()
        self.assertEqual(len(result["samples"]), 33)
        self.assertLessEqual(D(result["max_precision_error"]), D("1e-70"))
        self.assertLessEqual(D(result["max_ode_residual"]), D("1e-65"))

    def test_every_scalar_catalog_input_is_pinned_before_evaluation(self):
        original = json.loads((reference.HERE / "cases.json").read_bytes())

        def leaves(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from leaves(child, (*path, key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from leaves(child, (*path, index))
            else:
                yield path, value

        probes = 0
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cases.json"
            for address, value in leaves(original):
                changed = copy.deepcopy(original)
                target = changed
                for key in address[:-1]:
                    target = target[key]
                target[address[-1]] = (
                    value + 1 if isinstance(value, (int, float)) else value + "x"
                )
                path.write_text(json.dumps(changed, indent=2) + "\n")
                with (
                    self.subTest(address=address),
                    self.assertRaisesRegex(ValueError, "catalog bytes"),
                ):
                    reference.catalog(path)
                probes += 1
            self.assertGreater(probes, 700)
            path.write_bytes((reference.HERE / "cases.json").read_bytes())
            self.assertEqual(len(reference.catalog(path)["cases"]), 11)

    def test_structural_and_irrelevant_mutations_fail_with_fresh_fingerprint(self):
        original = json.loads((reference.HERE / "cases.json").read_bytes())
        mutations = []
        for action in (
            "missing",
            "duplicate",
            "reordered",
            "extra",
            "boolean",
            "irrelevant_population",
        ):
            changed = copy.deepcopy(original)
            if action == "missing":
                changed["cases"].pop()
            elif action == "duplicate":
                changed["cases"].append(changed["cases"][0])
            elif action == "reordered":
                changed["cases"].reverse()
            elif action == "extra":
                changed["unrecognized"] = 1
            elif action == "boolean":
                changed["cases"][0]["parameters"]["basal"][0] = True
            else:
                # Equilibrium fluxes are zero, so this changes no state trajectory.
                changed["cases"][-2]["populations"][0] += 1
            mutations.append(changed)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cases.json"
            for changed in mutations:
                raw = (json.dumps(changed, indent=2) + "\n").encode()
                fresh_digest = hashlib.sha256(raw).hexdigest()
                self.assertNotEqual(fresh_digest, reference.CATALOG_SHA256)
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, "catalog bytes"):
                    reference.report(path)

    def test_irrelevant_input_changes_really_leave_analytical_laws_valid(self):
        cases = reference.catalog()["cases"]
        population = copy.deepcopy(cases[9])
        population["populations"][0] += 1
        paired_rates = copy.deepcopy(cases[9])
        paired_rates["parameters"]["export"][0][0] *= 2
        paired_rates["parameters"]["import"][0][0] *= 2
        disconnected_volume = copy.deepcopy(cases[4])
        disconnected_volume["medium_volume_L"] += 1
        for changed in (population, paired_rates, disconnected_volume):
            for time in (0, 1, 4):
                self.assertLessEqual(reference.residual(changed, time), D("1e-65"))

    def test_changed_repression_translation_and_exchange_break_analytical_laws(self):
        cases = reference.catalog()["cases"]
        for index, mutate in (
            (0, lambda c: c["parameters"]["hill_n"].__setitem__(0, 2)),
            (8, lambda c: c["parameters"]["translation"].__setitem__(0, 4)),
            (10, lambda c: c["parameters"]["export"][0].__setitem__(0, 2)),
        ):
            case = copy.deepcopy(cases[index])
            mutate(case)
            with self.subTest(case=case["id"]):
                self.assertGreater(reference.residual(case, 1), D("1e-4"))

    def test_repression_reads_intracellular_pool_without_consumption(self):
        case = reference.catalog()["cases"][4]
        y = reference.state(case["id"], 1)
        with localcontext() as ctx:
            ctx.prec = 80
            original = reference.rhs(case, y)
            changed_medium = y.copy()
            changed_medium[17] *= 3
            self.assertEqual(reference.rhs(case, changed_medium), original)
            changed_gate = copy.deepcopy(case)
            changed_gate["parameters"]["induced"][0] *= 2
            delta = [
                b - a
                for a, b in zip(original, reference.rhs(changed_gate, y), strict=True)
            ]
            self.assertGreater(delta[0], 0)
            self.assertTrue(all(value == 0 for value in delta[1:]))

    def test_exact_heterogeneous_weighted_conservation_for_all_signals(self):
        case = reference.catalog()["cases"][-1]
        with localcontext() as ctx:
            ctx.prec = 160
            for time in (0, 1, 4):
                y = reference.state(case["id"], time)
                dy = reference.rhs(case, y)
                for k in range(3):
                    mass = y[15 + k] + sum(
                        D(n) * y[6 + 3 * j + k] for j, n in enumerate([3, 5, 7])
                    )
                    initial_mass = D(56 * (k + 2) + 12 * (k + 6))
                    self.assertLessEqual(abs(mass - initial_mass), D("1e-150"))
                    drift = dy[15 + k] + sum(
                        D(n) * dy[6 + 3 * j + k] for j, n in enumerate([3, 5, 7])
                    )
                    self.assertLessEqual(abs(drift), D("1e-150"))


if __name__ == "__main__":
    unittest.main()
