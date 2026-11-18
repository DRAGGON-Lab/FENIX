using Test
include(joinpath(@__DIR__,"run.jl"))
@testset "M0 benchmark failure controls" begin
    @test isnothing(validate_values("linear-production",[0.5,1.5,2.5,20.5]))
    @test_throws ErrorException validate_values("linear-production",[0.5,1.5,2.5,20.6])
    for values in ([0.5], fill(NaN,4), fill(Inf,4), fill(-1e-320,4))
        @test_throws ErrorException validate_values("linear-production",values)
    end
    for samples in (Float64[],[NaN],[Inf],[-0.1])
        @test_throws ErrorException summary(samples)
    end
    @test summary([0.0,2.0,1.0])["median"]==1.0
end
