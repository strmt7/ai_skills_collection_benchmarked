# Qualification

The [28 selected-tool controls](../../../../../artifacts/research/2026-10-07/mutation-tool-runtime-controls.json)
include a real bounded mutmut campaign, a real offline Trailmark Python graph,
executed source-example defects, host-side denominator/cleanup rejection, and
two mathematical inverse-mapping examples. They do not benchmark this skill's
effect on a coding agent.

The math examples use moduli 19 and 65521, byte limbs and nontrivial invertible
Montgomery factors. Canonical public inputs map to different internal residues
1 and 2 with shared high limbs, distinguishing AND from OR of limb equality.
The host recomputes the mappings and limb results. These generic constructions
challenge universal impossibility; the case-study Rust library was not executed.
Its actual conversion and API domain require a separate integration test.

Both original package texts were completely read. The current upstream delta
replaces old Wycheproof formatting advice with `vectorgen`, but retains the
Montgomery claim and general vector/triage issues recorded in the research note.
The pinned [Wycheproof contribution guide](https://github.com/C2SP/wycheproof/blob/12fd3aaf33eb5fa1f52e026912ee00c054f9d984/doc/vectorgen.md)
was fetched and read for its workflow; the Go CLI was not executed here.

The six-mutant threshold campaign changes one survivor to killed after explicit
boundary assertions while five mutants remain untested. This illustrates
controlled result accounting, not cryptographic-library quality. Rust/native
mutation, Necessist, complete crypto vector generation and independent agent
comparison remain unqualified. See the separately qualified Wycheproof overlay
for its selected AES-GCM/Ed25519 provider scopes and exclusions.
