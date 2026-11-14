using Test
using Fenix

@testset "FENIX Julia scaffold" begin
    @test isdefined(Fenix, :SCAFFOLD_ONLY)
    @test Fenix.SCAFFOLD_ONLY === true
end
