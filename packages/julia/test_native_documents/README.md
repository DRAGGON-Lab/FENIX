# Native Julia P01 document conformance

Run from the repository root in the pinned reference-tool environment:

```sh
JULIA_PKG_OFFLINE=true julia --project=conformance/julia packages/julia/test_native_documents/runtests.jl --report artifacts/julia-native-documents.json
```

The native package independently consumes original approved input bytes. The
runner only dispatches operations, labels supplied inputs and verifies catalog
checksums; it does not implement validation, identity or scientific rules.

Coverage: all 92 original P01 cases and the overlapping 97 P01 cases from the
rejection catalog. Original SCHEMA paths are coarsened to the catalog's root-only
expectation only during comparison; the 97-case subset checks exact categories,
paths and document labels. Parse values, binary64 bit patterns and canonical
text are checked where specified. Accepted exports are independently checked by
JSONSchema. The remaining 110 FIR/P03 rejection cases are outside this suite.

Additionally checks the 27 approved binary64 JCS serialization vectors directly
from fixed bit patterns and expected bytes. This does not run FIR normalization,
validate mathematical FIR or establish cross-language compiler/solver acceptance.

The optional report is emitted only after all tests pass, and identifies native
runtime, catalog hashes and observed case outcomes. Package unit tests remain
independent of this checkout and its fixtures.
