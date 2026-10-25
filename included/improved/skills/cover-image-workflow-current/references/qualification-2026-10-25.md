# Qualification snapshot, 25 October 2026

For real image work, use the available qualified image tool. The historical
CLI is a source-locked comparison and maintenance input. Its current npm
publication is still 1.0.17. The aggregator removed its tracked copy on 18 May;
that removal does not establish a new implementation or a repaired publication.

Google's [current image model page](https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1?hl=en)
identifies `gemini-nano-banana-2.1` as stable. Its
[lifecycle table](https://ai.google.dev/gemini-api/docs/deprecations) recommends
that replacement for `gemini-3.1-flash-image`; the older stable model has no
announced shutdown date. The CLI's `gemini-3.1-flash-image-preview` has a listed
25 June 2026 shutdown. Recheck the specific model and lifecycle pages before a
real request. A documentation check does not establish account access or image
quality. This repair deliberately retains the historical provider configuration
as an unqualified maintenance input.

The [SDK ImageConfig interface](https://googleapis.github.io/js-genai/release_docs/interfaces/types.ImageConfig.html)
at GenAI 2.31.0 has no `numberOfImages` field for GenerateContent. Some properties
in that interface are explicitly unsupported by the Gemini API. Check the
particular API and model instead of treating all SDK fields as interchangeable.

The repaired package pins GenAI 2.31.0, Inquirer Prompts 8.7.4, Chalk 6.0.1,
Commander 15.0.0, Conf 16.0.0, Dotenv 18.0.9, Figlet 1.12.0, Gradient String
3.0.0 and Sharp 0.35.5. These were the primary registry's latest stable direct
versions at review. Node 26.12.1/npm 12.2.1 installed the complete lock normally
with lifecycle scripts disabled. The graph passed its advisory audit and the
43 existing CLI controls. Transitive `glob` and `node-domexception` deprecation
warnings remain visible; zero known advisories does not erase those warnings.

The [explicit repair](cli-repair.md) additionally passes fourteen independent
download/resource controls, including actual loopback HTTP. The same evaluator
ran against the original code with the same current graph before repair.
Results are component checks, not fourteen independent image-generation tasks
or a measure of agent improvement. The earlier [snapshot](qualified-implementation.md)
and all failed measurements remain historical evidence.

All twenty mirrored resources were reviewed. The eight examples decode as
1200 × 630 images, not 16:9. They illustrate typography and layout; no original
task prompts establish them as exact-title or logo ground truth. Inspect the
actual requested output rather than using these examples as a passing oracle.
The copied source publishing workflow is archival: its unpinned actions, old
runtime and token-based release instructions are not a qualified release recipe.

Credential persistence, actual provider availability and visual fidelity remain
unqualified. The downloader's bounds do not provide DNS-based network isolation
or a process sandbox. Source review and local controls cannot establish those
separate properties, or the skill's efficacy for a coding agent.
