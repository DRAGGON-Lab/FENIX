"""Native authoring behavior; runs with the wheel and no development tools."""

import dataclasses
import json
import math
import unittest
from decimal import Decimal
from fractions import Fraction
from typing import Any

from fenix.bioir import (
    BioIRValidationError,
    Compartment,
    DesignContent,
    DesignReference,
    ExperimentContent,
    Function,
    InitialCount,
    Observable,
    Parameter,
    ParameterAssignment,
    Port,
    PortReference,
    Quantity,
    Species,
)


def design(**changes: Any) -> DesignContent:
    args = dict(
        id="design",
        revision=1,
        compartments=(Compartment(id="cell", volume=Quantity(value=1e-15, unit="L")),),
        species=(Species(id="x", compartment="cell", ports=(Port(id="amount"),)),),
        parameters=(
            Parameter(id="alpha", unit="molecule/s"),
            Parameter(id="beta", unit="1/s"),
        ),
        functions=(
            Function(
                id="production",
                kind="constitutive_production",
                target=PortReference(species="x", port="amount"),
                parameter="alpha",
            ),
            Function(
                id="decay",
                kind="first_order_decay",
                target=PortReference(species="x", port="amount"),
                parameter="beta",
            ),
        ),
    )
    args.update(changes)
    return DesignContent(**args)


def experiment(**changes: Any) -> ExperimentContent:
    args = dict(
        id="experiment",
        revision=1,
        source_design=design(),
        design=DesignReference(id="design", revision=1, digest="0" * 64),
        parameters=(
            ParameterAssignment(
                parameter="alpha", quantity=Quantity(value=10, unit="molecule/s")
            ),
            ParameterAssignment(
                parameter="beta", quantity=Quantity(value=0.1, unit="1/s")
            ),
        ),
        initial_counts=(
            InitialCount(species="x", quantity=Quantity(value=0.5, unit="molecule")),
        ),
        observables=(
            Observable(id="amount_x", target=PortReference(species="x", port="amount")),
        ),
        interventions=(),
    )
    args.update(changes)
    return ExperimentContent(**args)


class TestContent(unittest.TestCase):
    def error(self, category: str, path: str, fn: Any, **args: Any) -> None:
        with self.assertRaises(BioIRValidationError) as caught:
            fn(**args)
        self.assertEqual(
            (caught.exception.category, caught.exception.path), (category, path)
        )
        self.assertTrue(str(caught.exception))
        self.assertIsInstance(caught.exception, ValueError)

    def test_positive_serialization_and_order(self) -> None:
        d = design()
        reordered = design(parameters=d.parameters[::-1], functions=d.functions[::-1])
        self.assertEqual(reordered.to_dict()["parameters"][0]["id"], "beta")
        self.assertEqual(reordered.to_dict()["functions"][0]["id"], "decay")
        for obj in (d, reordered, experiment(), experiment(observables=())):
            self.assertEqual(json.loads(obj.to_json()), obj.to_dict())
            self.assertNotIn("content", obj.to_dict())
            self.assertNotIn("source_design", obj.to_dict())
            self.assertNotIn("digest", obj.to_dict())
        e = experiment()
        self.assertEqual(e.to_dict()["initial_counts"][0]["quantity"]["value"], 0.5)
        self.assertEqual(
            list(e.to_dict()),
            [
                "kind",
                "schema_version",
                "id",
                "revision",
                "design",
                "parameters",
                "initial_counts",
                "observables",
                "interventions",
            ],
        )

    def test_immutable_and_fresh_outputs(self) -> None:
        d = design()
        for obj, name in (
            (d, "id"),
            (d.species[0], "id"),
            (d.compartments[0].volume, "value"),
            (experiment().design, "digest"),
        ):
            with self.assertRaises(dataclasses.FrozenInstanceError):
                setattr(obj, name, "changed")
            self.assertFalse(hasattr(obj, "__dict__"))
        a = d.to_dict()
        a["species"][0]["ports"][0]["id"] = "mutated"
        a["functions"].clear()
        self.assertEqual(d.to_dict()["species"][0]["ports"][0]["id"], "amount")
        self.assertEqual(len(d.functions), 2)
        e = experiment()
        a = e.to_dict()
        a["parameters"][0]["quantity"]["value"] = 999
        a["design"]["id"] = "changed"
        self.assertEqual(e.to_dict()["parameters"][0]["quantity"]["value"], 10)
        self.assertEqual(e.design.id, "design")

    def test_ids_revisions_and_tokens(self) -> None:
        for value in ("", "1x", "é", "a\n", "a/b", "a" * 65, None, 1):
            self.error("SCHEMA", "/id", Port, id=value)
        self.assertEqual(Port(id="A_a-0").id, "A_a-0")
        self.assertEqual(Port(id="a" * 64).id, "a" * 64)
        for value in (0, -1, True, 1.0, 2**53, "1"):
            self.error("SCHEMA", "/revision", design, revision=value)
        self.assertEqual(design(revision=2**53 - 1).revision, 2**53 - 1)
        self.error("SCHEMA", "/kind", Port, id="p", kind="concentration")
        self.error("SCHEMA", "/kind", design, kind="Experiment")
        self.error("SCHEMA", "/schema_version", experiment, schema_version="2")
        self.error(
            "SCHEMA",
            "/kind",
            Function,
            id="f",
            kind="callback",
            target=PortReference(species="x", port="p"),
            parameter="a",
        )
        for digest in ("A" * 64, "0" * 63, "0" * 64 + "\n", 0):
            self.error(
                "SCHEMA", "/digest", DesignReference, id="d", revision=1, digest=digest
            )

    def test_native_numeric_policy(self) -> None:
        for value in (True, False, "1", None, Decimal("1"), Fraction(1, 2), complex(1)):
            self.error("SCHEMA", "/value", Quantity, value=value, unit="molecule")
        for value in (float("nan"), float("inf"), -float("inf")):
            self.error("NUMBER_RANGE", "/value", Quantity, value=value, unit="molecule")
        for value in (2**53, -(2**53), 10**400):
            self.error(
                "INTEGER_RANGE", "/value", Quantity, value=value, unit="molecule"
            )
        self.error("SCHEMA", "/value", Quantity, value=-5e-324, unit="molecule")
        for value in (
            0,
            -0.0,
            5e-324,
            2**53 - 1,
            float(2**53),
            float.fromhex("0x1.fffffffffffffp+1023"),
        ):
            q = Quantity(value=value, unit="molecule/s")
            self.assertEqual(q.value, value)
            self.assertIs(type(q.value), type(value))
            e = experiment(
                parameters=(
                    ParameterAssignment(parameter="alpha", quantity=q),
                    ParameterAssignment(
                        parameter="beta", quantity=Quantity(value=0, unit="1/s")
                    ),
                )
            )
            readback = json.loads(e.to_json())["parameters"][0]["quantity"]["value"]
            self.assertEqual(readback, value)
            if type(value) is float and value == 0:
                self.assertEqual(math.copysign(1, readback), math.copysign(1, value))
        self.error(
            "SCHEMA",
            "/volume/value",
            Compartment,
            id="c",
            volume=Quantity(value=0, unit="L"),
        )
        self.assertEqual(
            Compartment(id="c", volume=Quantity(value=5e-324, unit="L")).volume.value,
            5e-324,
        )

    def test_units(self) -> None:
        self.error("SCHEMA", "/unit", Quantity, value=1, unit="mol/L")
        self.error("SCHEMA", "/unit", Parameter, id="a", unit="molecule")
        self.error(
            "SCHEMA",
            "/volume/unit",
            Compartment,
            id="c",
            volume=Quantity(value=1, unit="molecule"),
        )
        self.error(
            "SCHEMA",
            "/quantity/unit",
            InitialCount,
            species="x",
            quantity=Quantity(value=1, unit="L"),
        )
        self.error(
            "SCHEMA",
            "/quantity/unit",
            ParameterAssignment,
            parameter="a",
            quantity=Quantity(value=1, unit="molecule"),
        )
        d = design()
        self.error(
            "UNIT",
            "/functions/0/parameter",
            design,
            parameters=tuple(dataclasses.replace(p, unit="1/s") for p in d.parameters),
        )
        e = experiment()
        self.error(
            "UNIT",
            "/parameters/0/quantity/unit",
            experiment,
            parameters=(
                dataclasses.replace(
                    e.parameters[0], quantity=Quantity(value=1, unit="1/s")
                ),
                e.parameters[1],
            ),
        )

    def test_tuples_types_and_cardinalities(self) -> None:
        d = design()
        for name in ("compartments", "species", "parameters", "functions"):
            self.error("SCHEMA", "/" + name, design, **{name: list(getattr(d, name))})
            self.error("SCHEMA", "/" + name, design, **{name: ()})
            self.error("SCHEMA", "/" + name, design, **{name: getattr(d, name) * 2})
            self.error(
                "SCHEMA",
                "/" + name + "/0",
                design,
                **{name: ({},) + getattr(d, name)[1:]},
            )
        self.error("SCHEMA", "/ports", Species, id="x", compartment="c", ports=[])
        self.error("SCHEMA", "/ports", Species, id="x", compartment="c", ports=())
        self.error("SCHEMA", "/ports/0", Species, id="x", compartment="c", ports=({},))
        self.error(
            "SCHEMA",
            "/target",
            Observable,
            id="o",
            target={"species": "x", "port": "p"},
        )
        self.error(
            "SCHEMA", "/volume", Compartment, id="c", volume={"value": 1, "unit": "L"}
        )
        e = experiment()
        for name in ("parameters", "initial_counts", "observables", "interventions"):
            self.error(
                "SCHEMA", "/" + name, experiment, **{name: list(getattr(e, name))}
            )
        self.error(
            "SCHEMA", "/interventions", experiment, interventions=({"event": "pulse"},)
        )
        self.error("SCHEMA", "/source_design", experiment, source_design={})
        self.error("SCHEMA", "/design", experiment, design={})

    def test_design_references_duplicates_and_roles(self) -> None:
        d = design()
        self.error(
            "REFERENCE",
            "/species/0/compartment",
            design,
            species=(dataclasses.replace(d.species[0], compartment="Cell"),),
        )
        for name in ("species", "port"):
            target = dataclasses.replace(d.functions[0].target, **{name: "unknown"})
            self.error(
                "REFERENCE",
                "/functions/0/target/" + name,
                design,
                functions=(
                    dataclasses.replace(d.functions[0], target=target),
                    d.functions[1],
                ),
            )
        self.error(
            "REFERENCE",
            "/functions/0/parameter",
            design,
            functions=(
                dataclasses.replace(d.functions[0], parameter="unknown"),
                d.functions[1],
            ),
        )
        for name in ("parameters", "functions"):
            values = getattr(d, name)
            self.error(
                "DUPLICATE_ID",
                "/" + name + "/1/id",
                design,
                **{name: (values[0], values[0])},
            )
        self.error(
            "FUNCTION_ROLE",
            "/functions/1",
            design,
            functions=(d.functions[0], dataclasses.replace(d.functions[0], id="other")),
        )

    def test_experiment_context_and_references(self) -> None:
        e = experiment()
        for name, value in (("id", "unknown"), ("revision", 2)):
            self.error(
                "DESIGN_REFERENCE",
                "/design/" + name,
                experiment,
                design=dataclasses.replace(e.design, **{name: value}),
            )
        # Digest syntax only: #19 will verify correspondence and trusted identity.
        self.assertEqual(
            experiment(
                design=dataclasses.replace(e.design, digest="f" * 64)
            ).design.digest,
            "f" * 64,
        )
        self.error(
            "DUPLICATE_ID",
            "/parameters/1/parameter",
            experiment,
            parameters=(e.parameters[0], e.parameters[0]),
        )
        self.error(
            "REFERENCE",
            "/parameters/0/parameter",
            experiment,
            parameters=(
                dataclasses.replace(e.parameters[0], parameter="unknown"),
                e.parameters[1],
            ),
        )
        self.error(
            "REFERENCE",
            "/initial_counts",
            experiment,
            initial_counts=(
                dataclasses.replace(e.initial_counts[0], species="unknown"),
            ),
        )
        self.error(
            "DUPLICATE_ID",
            "/observables/1/id",
            experiment,
            observables=e.observables * 2,
        )
        for name in ("species", "port"):
            target = dataclasses.replace(e.observables[0].target, **{name: "unknown"})
            self.error(
                "REFERENCE",
                "/observables/0/target/" + name,
                experiment,
                observables=(dataclasses.replace(e.observables[0], target=target),),
            )

    def test_argument_binding(self) -> None:
        for name in (
            "profile",
            "callback",
            "time_grid",
            "solver",
            "events",
            "metadata",
            "digest",
        ):
            with self.assertRaises(TypeError):
                experiment(**{name: "unsupported"})
        with self.assertRaises(TypeError):
            Port("p")  # type: ignore[misc]
        with self.assertRaises(TypeError):
            Quantity(unit="molecule")  # type: ignore[call-arg]


if __name__ == "__main__":
    unittest.main()
