# C++ correctness and performance references

Two selected C++ reference skills have received a complete read of their three
packaged resources and a comparison with current upstream instructions. This
is source research; no native-code execution or coding-agent gain is counted.

The parity guide keeps a frozen behavior reference. Preserve that oracle and
define observable outputs, errors, ordering and numeric rules before optimizing.
Both packages assume their original project's directories and refer to other
skills outside these packages. Resolve those dependencies before independent use.

The performance guide already conditions views, moves and concurrency on
correctness and lifetime requirements. The [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
support measurement before optimization and attention to allocation and layout.
The cited [reserve reference](https://en.cppreference.com/cpp/container/vector/reserve)
also explains invalidation and why repeated reservation can hurt performance.
The [move-constructor reference](https://en.cppreference.com/cpp/language/move_constructor)
qualifies move/copy selection and exception guarantees. The old reference URLs
redirected; those captures were retained and rejected before explicit canonical
URLs were successfully captured with the same strict Crawl4AI provider.

For a comparison, bind both measurements to exact source, build options, inputs,
timing boundaries and repeated observations. Keep absolute times and uncertainty;
a difference inside noise remains inconclusive. Current upstream clarifies the
Python/native speedup ratio and labels values below one as regressions.
[pyperf's system guidance](https://pyperf.readthedocs.io/en/latest/system.html)
also distinguishes platform-specific noise and tuning considerations. Reading
those instructions does not authorize changing a host's power or scheduling
policy during unrelated work; no such setting was changed here.

The repository API identified no licence, and the inspected parent directories
had no licence-named file. Its README credits a BSD-licensed upstream snapshot;
the redistribution basis for these newer skill resources remains unclassified.
No derivative overlay or mirror update was published in this research batch.

The [review record](../artifacts/research/cpp-contracts/cpp-review.json) binds
every packaged resource, upstream comparison and admitted reference capture.
Portable dependency resolution, redistribution evidence, independent runtime
contracts and measured coding-agent benefit remain open in the improvement ledger.
