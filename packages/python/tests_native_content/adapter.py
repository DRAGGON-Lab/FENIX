"""Test-only structural projection into public constructors, never a validator.

The fixture JSON decoder is ordinary json.loads. Only selected, already approved
content inputs are used. This does not test native parsing or committed envelopes.
"""

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


class ProjectionError(Exception):
    def __init__(self, error: BioIRValidationError, prefix: str) -> None:
        self.error = error
        self.prefix = prefix
        self.document_path = prefix + error.path
        super().__init__(str(error))


# Entries describe constructor nesting only, with no scientific assertions.
_CHILDREN: dict[type[Any], dict[str, tuple[type[Any], bool]]] = {
    Compartment: {"volume": (Quantity, False)},
    Species: {"ports": (Port, True)},
    Function: {"target": (PortReference, False)},
    ParameterAssignment: {"quantity": (Quantity, False)},
    InitialCount: {"quantity": (Quantity, False)},
    Observable: {"target": (PortReference, False)},
    DesignContent: {
        "compartments": (Compartment, True),
        "species": (Species, True),
        "parameters": (Parameter, True),
        "functions": (Function, True),
    },
    ExperimentContent: {
        "design": (DesignReference, False),
        "parameters": (ParameterAssignment, True),
        "initial_counts": (InitialCount, True),
        "observables": (Observable, True),
    },
}


def construct(
    cls: type[Any], raw: dict[str, Any], prefix: str = "/content", **context: Any
) -> Any:
    args = raw.copy()
    for name, (child, repeated) in _CHILDREN.get(cls, {}).items():
        path = prefix + "/" + name
        if repeated:
            args[name] = tuple(
                construct(child, item, path + f"/{i}")
                for i, item in enumerate(raw[name])
            )
        else:
            args[name] = construct(child, raw[name], path)
    if cls is ExperimentContent:
        args["interventions"] = tuple(raw["interventions"])
    args.update(context)
    try:
        return cls(**args)
    except BioIRValidationError as error:
        raise ProjectionError(error, prefix) from error
