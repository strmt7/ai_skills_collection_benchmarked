# Genotoxic and Vector Forge review in progress

Both entrypoints, Genotoxic's graph and triage references, and Vector Forge's
fault simulation, vector patterns, case-study lessons and report template were
read completely. Both long mutation-framework references remain pending. This
is a source/contract review; neither mutation campaigns nor agent comparisons
have been executed for these packages.

Genotoxic and Vector Forge can dismiss findings solely because a static graph
has no callers or cannot map a location. An exported entrypoint can have no
in-repository caller; dynamic callbacks and incomplete language/import/path
resolution can also omit edges. Graph absence needs an unresolved category and
scope evidence, not automatic false-positive status or code removal.

Genotoxic's necessist mapper can choose the first candidate after ambiguous
name matching. Its test-path substring filter can exclude production paths, and
its merge consumes a function's removal list for only the first matching mutant.
Use explicit identities, preserve ambiguity and retain complete case accounting.
Same-function signals are useful prioritization evidence, not proof of a shared
missing assertion. Cleanup removals may leave leaks or contamination despite
passing immediate assertions.

Equivalence needs a stated type/input/side-effect contract. Unary plus and
commutativity are not universal for overloaded operations or arbitrary values.
Logging/error formatting may be an externally consumed contract. Complexity and
caller thresholds are heuristics, not security severity or proof that fuzzing
subsumes focused regression tests. Preserve reproducing regression cases and
an appropriate oracle alongside fuzzing.

Vector Forge's reported campaign counts are upstream case-study claims, not
reproduced results here. Before/after mutation comparisons need frozen mutant
identities, source and tests, complete status denominators, and comparable
selection/time/resource policies. A coverage ratio derived merely from mutant
statuses is not measured source coverage. FFI wrapper behavior can have its own
contract even when implementation arithmetic lives elsewhere. Cross-package
test selection is an untested scope until rerun, rather than an automatically
discharged finding.

Cryptographic vector expectations must come from the specific protocol/API
contract. Identity points, zero scalars, duplicate aggregate messages, implicit
rejection and accepted noncanonical encodings are not governed by one generic
invalid/roundtrip rule. Two implementations can share a backend or a bug; their
agreement needs specification and independence evidence. Smaller limb models
must preserve the same mathematical field and operation before exporting a
full-width vector. A case distinguishing one injected model fault does not
establish coverage of that whole fault class in production.

The blanket claim that public inputs cannot target matching Montgomery limbs
requires investigation: multiplication by an invertible Montgomery factor is
a bijection modulo the field/order. For an API that accepts canonical scalars,
inverse mapping can select a desired representable internal residue. This is
an analytical objection, not an executed claim about the case-study library.

Primary version checks resolve Trailmark 0.5.0 at
`6ee0f2252d7d5ceed31210491332a553c1af4b23` and mutmut 3.8.0 at
`14a7230049a5c8abd90c2bb0f7438e30da6471f5`. The fetched Trailmark API confirms
that `to_json()` supplies a node dictionary and that the displayed
`complexity_hotspots(threshold=...)` and `attack_surface()` fields are supported;
those examples must not be declared broken speculatively. Mutmut's pinned
README describes POSIX fork requirements and `tool.mutmut.source_paths`
configuration. The skills' old CLI flags still require executable qualification.

Remaining work: complete both framework-reference reviews, inspect newer
upstream resources, run bounded current tool/source controls, produce licensed
overlays from demonstrated defects, and evaluate independent coding tasks.
