# Independent BigFloat analytical evaluator. No native FENIX imports.
using JSON
function samples(bits)
    setprecision(BigFloat,bits) do
        output = Dict{String,Any}[]
        for n in 1:4, time in (0,1,4)
            # Solve y' = 2-y/2, y(0)=0 under constant threshold sensing.
            y = 4*(-expm1(-BigFloat(time)/2))
            push!(output,Dict("case"=>"threshold-n$n","time"=>time,
                 "state"=>BigFloat[4,12,24,y]))
        end
        for time in (0,1,4)
            # Derive extracellular relaxation first from E' = 72-(5/2)E.
            e = BigFloat(24)+BigFloat(24)/5*(-expm1(-BigFloat(5)*time/2))
            s = (BigFloat(36)-e)/3
            push!(output,Dict("case"=>"reversible-transient","time"=>time,
                 "state"=>BigFloat[s,2,e,0]))
        end
        output
    end
end
low,high=samples(512),samples(1024)
setprecision(BigFloat,1024) do
    for (a,b) in zip(low,high)
        @assert all(abs(x-y)<=big"1e-140"*max(1,abs(y)) for (x,y) in zip(a["state"],b["state"]))
    end
    python=JSON.parsefile(ARGS[1])
    @assert length(python["samples"])==length(high)==15
    for (a,b) in zip(python["samples"],high)
        @assert a["case"]==b["case"] && a["time"]==b["time"]
        @assert all(abs(parse(BigFloat,x)-y)<=big"1e-150"*max(1,abs(y))
                    for (x,y) in zip(a["state"],b["state"]))
    end
end
println("PASS: 15 analytical samples, Julia 512/1024-bit refinement and Python agreement")
