# Keep generated evidence away from approved inputs, sources and their aliases.
function report_destination(path)
    destination = abspath(path)
    existing = destination
    suffix = String[]
    while !ispath(existing)
        islink(existing) && error("report destination must not use a dangling symlink")
        parent = dirname(existing)
        parent == existing && error("cannot resolve report destination")
        pushfirst!(suffix,basename(existing))
        existing = parent
    end
    resolved = joinpath(realpath(existing),suffix...)
    root = realpath(ROOT)
    artifact_root = joinpath(root,"artifacts")
    if (resolved == root || startswith(resolved,root * "/")) && !startswith(resolved,artifact_root * "/")
        error("report destination inside repository must be under artifacts/")
    end
    if ispath(destination)
        isfile(destination) || error("report destination must be a file")
        stat(destination).nlink == 1 || error("report destination must not be a hardlink alias")
    end
    resolved
end
