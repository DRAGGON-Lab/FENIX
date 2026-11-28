# Native M1 cross-language conformance

Refs #35. The local gate passed using the runtime-only Python wheel from
[#97](https://github.com/DRAGGON-Lab/FENIX/pull/97) and a separately extracted
Julia package from [#98](https://github.com/DRAGGON-Lab/FENIX/pull/98). The tested
installed source and schema bytes matched both implementation commits. The Julia
package loaded from the extracted path, and both locks used by Julia matched those
in the approved tree before and after the runs.

Across 80 runs, both languages produced the accepted canonical model and
identity bytes and independently verified all 80 peer records. The independent
comparator passed 240 four-state reference samples, 144 closed weighted-balance
samples, and 240 pairwise samples. The largest state-error/bound ratio was
0.06057. The largest balance-error/bound ratio was below 0.000000119.
Altered archive locks, missing peer rows and a numerically wrong trajectory with
recomputed checksums all failed their intended checks.

The [local comparison](m1-native-conformance/local-comparison.json) and
[receipt](m1-native-conformance/local-receipt.json) record the measured ratios,
artifact hashes and exact commands. The producer receipts retain their original
local preflight label. The receipt binds the installed sources to the two
implementation commits and the independent comparison to the reviewed harness
revision. The [engineering review](m1-native-conformance/engineering-review.json)
records the repaired lock association and the additional revision rejection
probe.

The [hosted workflow](../../.github/workflows/native-community-integration.yml)
publishes full per-run artifacts with the tested merge revision. Ordered PR
review and the final EP-05 requirements remain open.
