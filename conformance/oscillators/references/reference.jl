# Independent analytical P09 evaluator; no Python, SciPy or native FENIX imports.
module P09References
using JSON, SHA

const CATALOG_SHA256 = "071615af6915854cb9ebb53990d44eafad967b88221bccfca285dcdc610d2355"

function catalog(path=joinpath(@__DIR__, "cases.json"))
    bytes = read(path)
    # Pin every declared input, including ones irrelevant along a given solution.
    @assert bytes2hex(sha256(bytes)) == CATALOG_SHA256 "catalog bytes differ"
    JSON.parse(String(bytes))
end

function state(id, time)
    t = BigFloat(time)
    if occursin("-driven-n", id)
        n = parse(Int, string(last(id)))
        rate = BigFloat(n)/2
        z = exp(-t/2)^n
        lost = -expm1(-rate*t)
        a = BigFloat(2)^n
        # Integrating factor, using a decaying exponential and log1p.
        integral = rate*t + log1p(a*z) - log1p(a)
        m = 2*z + lost/rate + 4/rate*(lost-a*z*integral)
        community = startswith(id, "community")
        y = zeros(BigFloat, community ? 18 : 6)
        y[1] = m
        y[community ? 9 : 6] = 8*exp(-t/2)
        community && (y[18] = 999)
        return y
    elseif id == "single-translation-cascade"
        m = [BigFloat(i+1)*exp(-i*t) for i in 1:3]
        # Factor the homogeneous decay rather than subtracting exponentials.
        p = [exp(-(i+1)*t)*(i+4+(i+2)*(i+1)*expm1(t)) for i in 1:3]
        return vcat(m, p)
    elseif id == "community-threshold-equilibrium"
        return BigFloat[ones(6)..., 2,2,2, 3,3,3, 5,5,5, 12,12,12]
    elseif id == "community-closed-transport"
        volumes, populations = [2,3,5], [3,5,7]
        capacity = sum(volumes .* populations)
        y = zeros(BigFloat, 18)
        z = exp(-BigFloat(capacity+12)*t/12)
        for k in 1:3
            mass = capacity*(k+1)+12*(k+5)
            equilibrium = BigFloat(mass)/(capacity+12)
            environment = 12*equilibrium+(12*(k+5)-12*equilibrium)*z
            intracellular_density = (mass-environment)/capacity
            for j in 1:3
                y[6+3*(j-1)+k] = volumes[j]*intracellular_density
            end
            y[15+k] = environment
        end
        return y
    end
    error("unknown analytical case")
end

function rhs(case, y)
    p = case["parameters"]
    community = case["model"] == "three_strain_mrna_protein_exchange"
    v = community ? case["cell_volumes_L"] : fill(case["cell_volume_L"], 3)
    dy = zeros(BigFloat, length(y))
    for i in 1:3
        previous = mod1(i-1, 3)
        sensor = community ? y[6+3*(i-1)+previous] : y[3+previous]
        ratio = sensor/(BigFloat(v[i])*p["threshold_density"][i])
        inhibition = inv(1+ratio^p["hill_n"][i])
        dy[i] = p["basal"][i]+p["induced"][i]*inhibition-p["mrna_decay"][i]*y[i]
        dy[3+i] = p["translation"][i]*y[i]-p["protein_decay"][i]*y[3+i]
    end
    if community
        for j in 1:3, k in 1:3
            index = 6+3*(j-1)+k
            outgoing = p["export"][j][k]*y[index]
            incoming = BigFloat(p["import"][j][k])*v[j]*y[15+k]/case["medium_volume_L"]
            dy[index] = incoming-outgoing-p["intracellular_signal_decay"][j][k]*y[index]
            if j == k
                dy[index] += p["signal_synthesis"][k]*y[3+k]
            end
            dy[15+k] += case["populations"][j]*(outgoing-incoming)
        end
        for k in 1:3
            dy[15+k] -= p["medium_signal_decay"][k]*y[15+k]
        end
    end
    dy
end

function residual(case, time)
    h = BigFloat("1e-40")
    plus, minus = state(case["id"], BigFloat(time)+h), state(case["id"], BigFloat(time)-h)
    expected = rhs(case, state(case["id"], time))
    maximum(abs((a-b)/(2*h)-r)/max(1,abs(r)) for (a,b,r) in zip(plus,minus,expected))
end

function samples(data, bits)
    setprecision(BigFloat, bits) do
        output = []
        for case in data["cases"], time in case["times"]
            values = state(case["id"], time)
            @assert all(isfinite, values) && all(>=(0), values) "invalid analytical values"
            if time == 0
                @assert all(x == y for (x,y) in zip(values, case["initial_counts"])) "initial mismatch"
            end
            push!(output, (case["id"], time, values))
        end
        output
    end
end

function finite_nonnegative(text)
    @assert text isa AbstractString "reference numbers must be strings"
    value = parse(BigFloat, text)
    @assert isfinite(value) && value >= 0 "invalid reference number"
    value
end

function compare_report(report; catalog_path=joinpath(@__DIR__, "cases.json"))
    data = catalog(catalog_path) # Full fixed digest validation precedes report trust.
    low, high = samples(data, 512), samples(data, 1024)
    setprecision(BigFloat, 1024) do
        @assert Set(keys(report)) == Set(["status", "catalog_sha256", "samples",
            "max_precision_error", "max_ode_residual"]) "unexpected report fields"
        @assert report["status"] == "PROPOSED_ANALYTICAL"
        @assert report["catalog_sha256"] == CATALOG_SHA256 "wrong catalog fingerprint"
        @assert finite_nonnegative(report["max_precision_error"]) <= BigFloat("1e-70")
        @assert finite_nonnegative(report["max_ode_residual"]) <= BigFloat("1e-65")
        @assert length(report["samples"]) == length(high) == 33 "incomplete sample set"
        for (a,b,sample) in zip(low, high, report["samples"])
            id, time, values = b
            @assert all(abs(x-y) <= BigFloat("1e-140")*max(1,abs(y)) for (x,y) in zip(a[3],values)) "precision refinement"
            @assert Set(keys(sample)) == Set(["case", "time", "state"])
            @assert sample["case"] == id
            @assert sample["time"] isa Integer && !(sample["time"] isa Bool) && sample["time"] == time
            @assert length(sample["state"]) == length(values) "incomplete state vector"
            actual = finite_nonnegative.(sample["state"])
            @assert all(abs(x-y) <= BigFloat("1e-140")*max(1,abs(y)) for (x,y) in zip(actual,values)) "analytical disagreement"
        end
        largest_residual = maximum(residual(case,time) for case in data["cases"] for time in case["times"])
        @assert largest_residual <= BigFloat("1e-75") "closed form does not satisfy equations"
        println("PASS: 33 P09 analytical samples, refinement and equation residuals; candidate references only")
    end
end

end # module

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 1 || error("usage: reference.jl python-report.json")
    P09References.compare_report(P09References.JSON.parsefile(ARGS[1]))
end
