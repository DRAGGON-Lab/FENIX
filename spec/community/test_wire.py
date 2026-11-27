"""Positive/negative and independent-mathematical controls for the P08 packet."""

import copy
import hashlib
import json
import sys
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_wire
import wire_contract as wire

sys.path.insert(0, str(HERE.parents[1] / "conformance/community"))
import reference


class WireTests(unittest.TestCase):
    def setUp(self):
        self.d, self.e, self.f = review_wire.load(review_wire.FIXTURES / "threshold-n1")

    def test_complete_literal_catalog(self):
        report = review_wire.audit()
        self.assertEqual(
            report["counts"], {"positive": 13, "rejections": 56, "raw_numbers": 17}
        )
        self.assertEqual(report["native_implementation"], "NOT RUN")
        self.assertEqual(report["scientific_acceptance"], "PENDING")
        self.assertEqual(
            report["identities"]["renamed"], report["identities"]["threshold-n1"]
        )
        self.assertEqual(
            report["identities"]["permuted"], report["identities"]["threshold-n1"]
        )
        self.assertNotEqual(
            report["identities"]["empty-observables"],
            report["identities"]["threshold-n1"],
        )

    def test_normalization_is_fresh_idempotent_and_rejects_duplicate_ids(self):
        original = copy.deepcopy(self.f["model"])
        first = wire.normalize(original)
        self.assertEqual(first, wire.normalize(first))
        self.assertEqual(original, self.f["model"])
        first["initial_counts"]["sender.signal"]["value"] = 100
        self.assertEqual(original, self.f["model"])
        original["observables"].append(copy.deepcopy(original["observables"][0]))
        with self.assertRaises(wire.Rejection) as error:
            wire.normalize(original)
        self.assertEqual(error.exception.category, "DUPLICATE_ID")

    def test_every_rate_count_population_volume_affects_identity(self):
        before = wire.producer(self.d, self.e, self.f)[-1]
        for collection in ("parameters", "initial_counts", "populations", "volumes"):
            for key in self.f["model"][collection]:
                with self.subTest(collection=collection, key=key):
                    d, e, f = copy.deepcopy((self.d, self.e, self.f))
                    if collection == "populations":
                        e["content"][collection][key] += 1
                        f["model"][collection][key] += 1
                    else:
                        f["model"][collection][key]["value"] += 1
                        if collection == "volumes":
                            owner = next(
                                o for o in d["content"]["owners"] if o["role"] == key
                            )
                            owner["volume"]["value"] += 1
                            d["digest"] = wire.digest(d["content"])
                            e["content"]["design"]["digest"] = d["digest"]
                            f["provenance"]["design_digest"] = d["digest"]
                        else:
                            e["content"][collection][key]["value"] += 1
                    e["digest"] = wire.digest(e["content"])
                    f["provenance"]["experiment_digest"] = e["digest"]
                    self.assertNotEqual(wire.producer(d, e, f)[-1], before)

    def test_ast_reactions_match_independent_laws_at_all_reference_times(self):
        reference.validate_catalog(reference.catalog())
        with localcontext() as ctx:
            ctx.prec = 160
            for case in reference.catalog()["cases"]:
                _, _, fir = review_wire.load(review_wire.FIXTURES / case["id"])
                for time in case["times"]:
                    self.check_equations(
                        case, fir["model"], reference.state(case["id"], Decimal(time))
                    )
            # A separate asymmetric open-system point exercises all otherwise
            # disabled reaction terms and non-equilibrium signed transfers.
            case = copy.deepcopy(reference.catalog()["cases"][0])
            case["populations"], case["volumes"] = [7, 11], [2, 5, 13]
            case["parameters"].update(
                sender_decay=2,
                receiver_decay=3,
                env_decay=1,
                reporter_decay=2,
                sender_production=4,
                reporter_basal=3,
                sender_import=5,
                receiver_import=7,
                sender_export=3,
                receiver_export=2,
            )
            model = copy.deepcopy(self.f["model"])
            for key, value in case["parameters"].items():
                model["parameters"][key]["value"] = value
            model["populations"] = dict(
                zip(("sender", "receiver"), case["populations"], strict=True)
            )
            for key, value in zip(
                ("sender", "receiver", "env"), case["volumes"], strict=True
            ):
                model["volumes"][key]["value"] = value
            for n in range(1, 5):
                case["parameters"]["hill_n"] = n
                model["parameters"]["hill_n"]["value"] = n
                for e in (0, 13, 26, 52):
                    self.check_equations(case, model, list(map(Decimal, (4, 9, e, 2))))

    def check_equations(self, case, model, values):
        flux = {}
        bindings = {
            "state": dict(zip(reference.catalog()["state_ids"], values, strict=True)),
            "parameter": {
                k: Decimal(v["value"]) for k, v in model["parameters"].items()
            },
            "volume": {k: Decimal(v["value"]) for k, v in model["volumes"].items()},
            "population": {k: Decimal(v) for k, v in model["populations"].items()},
            "flux": flux,
        }

        def evaluate(node):
            if isinstance(node, (float, int)):
                return Decimal(node)
            op = node["op"]
            if op in bindings:
                return bindings[op][node["id"]]
            if op == "negate":
                return -evaluate(node["value"])
            if op == "hill":
                c, k, n = (
                    evaluate(node[key]) for key in ("density", "threshold", "exponent")
                )
                return c ** int(n) / (k ** int(n) + c ** int(n))
            a, b = evaluate(node["left"]), evaluate(node["right"])
            if op == "add":
                return a + b
            if op == "subtract":
                return a - b
            if op == "multiply":
                return a * b
            if op == "divide":
                return a / b
            raise ValueError(op)

        derivative = dict.fromkeys(reference.catalog()["state_ids"], Decimal(0))
        # Flux references are mathematical identifiers, never a declaration-order dependency.
        for reaction in model["reactions"]:
            flux[reaction["id"]] = evaluate(reaction["flux"])
        for reaction in model["reactions"]:
            for state, coefficient in reaction["stoichiometry"].items():
                derivative[state] += evaluate(coefficient) * flux[reaction["id"]]
        expected = dict(
            zip(
                reference.catalog()["state_ids"],
                reference.rhs(case, values),
                strict=True,
            )
        )
        for state, actual in derivative.items():
            self.assertLessEqual(
                abs(actual - expected[state]),
                Decimal("1e-140") * max(1, abs(expected[state])),
            )
        for equation in model["equations"]:
            value = expected[equation["state"]]
            self.assertLessEqual(
                abs(evaluate(equation["rhs"]) - value),
                Decimal("1e-140") * max(1, abs(value)),
            )

    def test_signed_zero_copy_and_exact_large_transport_counter(self):
        folder = review_wire.FIXTURES / "threshold-n1"
        raw = (folder / "zero.result.json").read_bytes()
        r = wire.decode(raw, "transport")
        m = review_wire.read(folder / "zero.python.manifest.json", "transport")
        self.assertEqual(m["execution"]["max_nfev"], 9007199254740993)
        # Serialized signed zeros survive decode, but direct observables must
        # preserve exactly the sign of their referenced state.
        r["state_values"][0][1] = -0.0
        r["observable_values"][0][1] = -0.0
        raw = (json.dumps(r) + "\n").encode()
        m["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
        wire.result_record(self.d, self.e, self.f, r, m, raw)
        r["observable_values"][0][1] = 0.0
        with self.assertRaises(wire.Rejection) as error:
            wire.result_record(self.d, self.e, self.f, r, m, raw)
        self.assertEqual(error.exception.category, "OBSERVABLE_COPY")

    def test_strict_utf8_and_invalid_encoded_inputs(self):
        for raw in (b"\xff", '{"value":1}'.encode("utf-16")):
            with self.assertRaises(wire.Rejection) as error:
                wire.decode(raw)
            self.assertEqual(error.exception.category, "JSON")


if __name__ == "__main__":
    unittest.main()
