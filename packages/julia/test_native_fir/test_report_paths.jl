@testset "Evidence output protects approved inputs and aliases" begin
    protected = joinpath(ROOT,"conformance/canonicalization/catalog.json")
    checksum = sha(read(protected))
    @test_throws ErrorException report_destination(protected)
    @test_throws ErrorException report_destination(joinpath(ROOT,"packages/julia/src/FIR.jl"))
    @test report_destination(joinpath(ROOT,"artifacts/new/report.json")) == joinpath(realpath(ROOT),"artifacts/new/report.json")
    mktempdir() do directory
        @test report_destination(joinpath(directory,"new.json")) == joinpath(realpath(directory),"new.json")
        symlink(protected,joinpath(directory,"symlink.json"))
        @test_throws ErrorException report_destination(joinpath(directory,"symlink.json"))
        symlink(dirname(protected),joinpath(directory,"linked-directory"))
        @test_throws ErrorException report_destination(joinpath(directory,"linked-directory/new.json"))
        symlink(joinpath(ROOT,"spec/__nonexistent_report.json"),joinpath(directory,"dangling.json"))
        @test_throws ErrorException report_destination(joinpath(directory,"dangling.json"))
        symlink(joinpath(ROOT,"spec/__nonexistent_directory"),joinpath(directory,"dangling-directory"))
        @test_throws ErrorException report_destination(joinpath(directory,"dangling-directory/report.json"))
        # External files with multiple links are also protected, regardless of
        # whether the alias names a repository or user-owned input.
        file = joinpath(directory,"original.json")
        write(file,"{}")
        hardlink(file,joinpath(directory,"hardlink.json"))
        @test_throws ErrorException report_destination(joinpath(directory,"hardlink.json"))
    end
    @test sha(read(protected)) == checksum
end
