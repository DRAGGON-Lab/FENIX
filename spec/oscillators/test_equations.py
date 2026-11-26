"""Independent mathematical corruption controls, without the candidate builders."""

import copy
import json
import tempfile
import unittest
from decimal import Decimal as D
from decimal import localcontext
from pathlib import Path
from unittest.mock import patch

import equation_audit as audit


def model(name):
    return json.loads((audit.HERE / "examples" / name / "fir.json").read_bytes())[
        "model"
    ]


def find(rows, role, key="id"):
    return next(row for row in rows if row[key] == role)


class TestIndependentEquations(unittest.TestCase):
    def test_all_cases_reaction_equation_reference_precision_and_exact_balance(self):
        report = audit.report()
        self.assertEqual(len(report["cases"]), 15)
        self.assertEqual(sum(len(row["evaluations"]) for row in report["cases"]), 186)
        self.assertEqual(
            sum(row["exact_transport_coefficient_checks"] for row in report["cases"]),
            432,
        )
        for row in report["cases"]:
            for point in row["evaluations"]:
                for value in point["max_scaled_differences"].values():
                    self.assertLessEqual(D(value), audit.ALGEBRA_LIMIT)

    def test_broken_mathematics_is_detected_without_schema_or_builder(self):
        _, _, probes = audit.cases()
        for fault in (
            "ring_direction",
            "medium_sensor",
            "translation_sink",
            "synthase_sink",
            "signal_owner",
            "swapped_rate",
            "equation_only",
        ):
            community = fault not in (
                "ring_direction",
                "translation_sink",
                "equation_only",
            )
            case = probes[1 if community else 0]
            candidate = audit.rebound(
                model("three-strain" if community else "single-cell"), case
            )
            reactions, equations = candidate["reactions"], candidate["equations"]
            if fault == "ring_direction":
                find(reactions, "repressed1")["flux"]["right"]["sensor"]["left"][
                    "id"
                ] = "p2"
            elif fault == "medium_sensor":
                sensor = find(reactions, "repressed1")["flux"]["right"]["sensor"]
                sensor["left"]["id"], sensor["right"]["id"] = "e3", "medium"
            elif fault == "translation_sink":
                find(reactions, "translation1")["stoichiometry"]["m1"] = -1
                equation = find(equations, "m1", "state")
                equation["rhs"] = {
                    "op": "subtract",
                    "left": equation["rhs"],
                    "right": {"op": "flux", "id": "translation1"},
                }
            elif fault == "synthase_sink":
                find(reactions, "synthesis1")["stoichiometry"]["p1"] = -1
                equation = find(equations, "p1", "state")
                equation["rhs"] = {
                    "op": "subtract",
                    "left": equation["rhs"],
                    "right": {"op": "flux", "id": "synthesis1"},
                }
            elif fault == "signal_owner":
                find(reactions, "synthesis1")["stoichiometry"] = {"a21": 1}
            elif fault == "swapped_rate":
                find(reactions, "export12")["flux"]["left"]["id"] = "out21"
            else:
                find(equations, "p1", "state")["rhs"]["right"]["id"] = "protein_decay2"
            with (
                self.subTest(fault=fault),
                self.assertRaisesRegex(ValueError, "disagreement"),
            ):
                audit.audit_case(candidate, case)

    def test_asymmetry_exposes_four_errors_hidden_in_primary(self):
        primary, components, probes = audit.cases()
        closed = next(c for c in components if c["id"] == "community-closed-transport")
        for fault in (
            "population_owner",
            "volume_owner",
            "transport_rate",
            "threshold",
        ):
            candidate = model("three-strain")
            if fault == "population_owner":
                find(candidate["reactions"], "export11")["stoichiometry"]["e1"][
                    "id"
                ] = "strain2"
                # Modify the equation too, preserving reaction/equation agreement.
                equation = find(candidate["equations"], "e1", "state")
                equation["rhs"]["left"]["left"]["left"]["left"]["id"] = "strain2"
            elif fault == "volume_owner":
                find(candidate["reactions"], "repressed1")["flux"]["right"]["sensor"][
                    "right"
                ]["id"] = "strain2"
            elif fault == "transport_rate":
                find(candidate["reactions"], "export12")["flux"]["left"]["id"] = "out21"
            else:
                find(candidate["reactions"], "repressed1")["flux"]["right"][
                    "threshold"
                ]["id"] = "K2"
            with self.subTest(fault=fault):
                audit.audit_case(
                    candidate, primary[1]
                )  # Symmetric primary values conceal each mutation.
                case = closed if fault == "population_owner" else probes[1]
                with self.assertRaises(ValueError):
                    audit.audit_case(audit.rebound(candidate, case), case)

    def test_unweighted_or_wrong_sign_transport_fails_exact_balance(self):
        _, _, probes = audit.cases()
        for value in (1, {"op": "negative_population", "id": "strain1"}):
            candidate = audit.rebound(model("three-strain"), probes[1])
            find(candidate["reactions"], "export11")["stoichiometry"]["e1"] = value
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "exact weighted transport balance"),
            ):
                audit.audit_case(candidate, probes[1])

    def test_all_projection_quantities_are_tied_to_the_pinned_definition(self):
        primary, _, _ = audit.cases()
        for fault in (
            "parameter",
            "parameter_unit",
            "parameter_basis",
            "volume",
            "population",
            "initial",
            "scope",
        ):
            candidate = model("three-strain")
            if fault == "parameter":
                find(candidate["parameters"], "b1")["value"] += 0.1
            elif fault == "parameter_unit":
                find(candidate["parameters"], "beta1")["unit"] = "molecule/s"
            elif fault == "parameter_basis":
                find(candidate["parameters"], "beta1")["basis"] = "first_order"
            elif fault == "volume":
                candidate["geometry"]["strain1"]["value"] *= 2
            elif fault == "population":
                candidate["populations"]["strain1"] += 1
            elif fault == "initial":
                candidate["states"][0]["initial"] += 1
            else:
                candidate["states"][0]["scope"] = "environment_total"
            with (
                self.subTest(fault=fault),
                self.assertRaisesRegex(ValueError, "differs"),
            ):
                audit.audit_case(candidate, primary[1])

    def test_unknown_operations_cycles_fields_and_stage_domains_are_rejected(self):
        primary, _, _ = audit.cases()
        candidate = model("single-cell")
        states = dict(zip(audit.reference_order(primary[0]), [D(1)] * 6, strict=True))
        for node in (
            {"op": "call", "callback": "untrusted"},
            {"op": "flux", "id": "translation1"},
            {"op": "state", "id": "p1", "callback": "untrusted"},
        ):
            with self.subTest(node=node), self.assertRaises(ValueError):
                audit.expression(node, candidate, states)
        states["p3"] = D(-1)
        with self.assertRaisesRegex(ValueError, "Hill sensor/domain"):
            audit.evaluated(candidate, states)
        for index, template, signed_role in (
            (0, "single-cell", "m1"),
            (1, "three-strain", "p2"),
        ):
            case = primary[index]
            states = dict.fromkeys(audit.reference_order(case), D(1))
            states[signed_role] = D(-1)
            with self.subTest(template=template), localcontext() as context:
                context.prec = 80
                aggregated, rhs = audit.evaluated(model(template), states)
                expected = dict(
                    zip(
                        audit.reference_order(case),
                        audit.oracle().rhs(
                            audit.lifted(case),
                            [states[r] for r in audit.reference_order(case)],
                        ),
                        strict=True,
                    )
                )
                audit.difference(aggregated, expected, "signed linear stage")
                audit.difference(rhs, expected, "signed linear stage")
            states[signed_role] = D("NaN")
            with self.assertRaisesRegex(ValueError, "nonfinite/misaligned"):
                audit.evaluated(model(template), states)

    def test_state_id_mapping_is_explicit_and_independent_of_declaration_order(self):
        primary, components, _ = audit.cases()
        candidate = model("three-strain")
        for key in ("states", "parameters", "reactions", "equations"):
            candidate[key].reverse()
        audit.audit_case(candidate, primary[1])
        case = copy.deepcopy(components[-1])
        case["state_ids"][0], case["state_ids"][6] = (
            case["state_ids"][6],
            case["state_ids"][0],
        )
        with self.assertRaisesRegex(ValueError, "reference state-ID/order"):
            audit.reference_order(case)

    def test_math_agreement_does_not_approve_serialized_template_equivalence(self):
        # Multiplication commutes mathematically. P10's separate structural
        # controls reject this noncanonical template; this audit cannot replace them.
        primary, _, _ = audit.cases()
        candidate = model("single-cell")
        flux = find(candidate["reactions"], "translation1")["flux"]
        flux["left"], flux["right"] = flux["right"], flux["left"]
        audit.audit_case(candidate, primary[0])

    def test_exact_binary64_lift_and_complete_input_pins(self):
        self.assertEqual(audit.decimal(0.1), D.from_float(0.1))
        self.assertNotEqual(audit.decimal(0.1), D("0.1"))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "equation-probes.json"
            path.write_bytes((audit.HERE / "equation-probes.json").read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "pinned input bytes"):
                audit.pinned(path, audit.PROBES_SHA256)
            source = Path(folder) / "reference.py"
            source.write_bytes(audit.REFERENCE.read_bytes() + b"\n")
            with (
                patch.object(audit, "REFERENCE", source),
                self.assertRaisesRegex(ValueError, "pinned P09 reference source"),
            ):
                audit.oracle()


if __name__ == "__main__":
    unittest.main()
