# Test-only structural projection into native constructors. This deliberately
# performs no scientific validation, parsing checks, or committed-document work.
module ContentProjection

using Fenix
const B = Fenix.BioIR

export ProjectionError, construct

struct ProjectionError <: Exception
    error::B.BioIRValidationError
    prefix::String
end

Base.showerror(io::IO, error::ProjectionError) = showerror(io, error.error)

const CHILDREN = Dict(
    B.Compartment => Dict(:volume => (B.Quantity, false)),
    B.Species => Dict(:ports => (B.Port, true)),
    B.BioIRFunction => Dict(:target => (B.PortReference, false)),
    B.ParameterAssignment => Dict(:quantity => (B.Quantity, false)),
    B.InitialCount => Dict(:quantity => (B.Quantity, false)),
    B.Observable => Dict(:target => (B.PortReference, false)),
    B.DesignContent => Dict(
        :compartments => (B.Compartment, true),
        :species => (B.Species, true),
        :parameters => (B.Parameter, true),
        :functions => (B.BioIRFunction, true),
    ),
    B.ExperimentContent => Dict(
        :design => (B.DesignReference, false),
        :parameters => (B.ParameterAssignment, true),
        :initial_counts => (B.InitialCount, true),
        :observables => (B.Observable, true),
    ),
)

pointer(parent, key) = parent * "/" * replace(string(key), "~" => "~0", "/" => "~1")

function construct(type, raw::AbstractDict; prefix="/content", context...)
    args = Dict{Symbol,Any}(Symbol(key) => value for (key, value) in raw)
    for (name, (child, repeated)) in get(CHILDREN, type, Dict())
        path = pointer(prefix, name)
        args[name] = if repeated
            Tuple(
                construct(child, item; prefix=pointer(path, index - 1))
                for (index, item) in enumerate(raw[string(name)])
            )
        else
            construct(child, raw[string(name)]; prefix=path)
        end
    end
    if type === B.ExperimentContent
        args[:interventions] = Tuple(raw["interventions"])
    end
    merge!(args, Dict{Symbol,Any}(context))
    try
        type(; args...)
    catch error
        error isa B.BioIRValidationError || rethrow()
        throw(ProjectionError(error, prefix))
    end
end

end # module ContentProjection
