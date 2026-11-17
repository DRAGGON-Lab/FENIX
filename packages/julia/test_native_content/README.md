# Native Julia content projections

Run from the repository root after instantiating the independent reference-tool
environment:

```sh
julia --project=conformance/julia packages/julia/test_native_content/runtests.jl
```

This suite constructs native uncommitted content from 29 approved P01 inputs
(6 acceptance controls and 23 rejection cases). The structural adapter contains
no semantic checks and invokes neither Python nor the reference validators.
It checks original input/dependency SHA-256 values, native categories and detailed
JSON Pointer paths, unchanged content output, ordinary JSON readback and the
ratified schema. JSONSchema is supplied by the test environment, not the library.

The coverage registry accounts for all 92 P01 cases: 29 `PROJECTED` and 63
`DEFERRED`, with reasons. Raw parsing, canonical bytes/digests, committed envelopes,
exact digest references and trusted revisions belong to #24. Metadata variants
exercise content only. These results do not establish full native document
conformance, authenticated identity, FIR/compiler behavior or biological validity.
Approved fixture bytes, expected outcomes and schemas remain unchanged.
