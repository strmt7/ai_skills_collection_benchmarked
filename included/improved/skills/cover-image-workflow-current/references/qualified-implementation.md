# Qualification snapshot, 2 October 2026

The historical CLI is an audited comparison input, not a recommended current
production implementation. Its minimal entrypoint has no workflow instructions.
The adjacent README overstates exact text enforcement, QA guarantees and private
credential storage. Its image endpoint is a preview identifier; consult the
provider's current stable model page and deprecation schedule before using it.

Google documents stable `gemini-3.1-flash-image` for image generation. Its
deprecation schedule lists the old image preview with a June 2026 shutdown date.
Current SDK ImageConfig has no `numberOfImages` property for GenerateContent;
do not mix its configuration with the separate GenerateImages API. Provider
documentation can differ in freshness: resolve the specific model page and
release/deprecation notices rather than assuming a generic guide is current.

- [Stable image model](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image)
- [Model lifecycle](https://ai.google.dev/gemini-api/docs/deprecations)
- [Current SDK ImageConfig](https://googleapis.github.io/js-genai/release_docs/interfaces/types.ImageConfig.html)

A complete staged graph resolves Google GenAI 2.26.0, Inquirer Prompts 8.7.2,
Chalk 6.0.1, Commander 15.0.0, Conf 15.1.0, Dotenv 18.0.5, Figlet 1.12.0,
Gradient String 3.0.0 and Sharp 0.35.5. Primary registry metadata identifies
these stable versions. Installation and mocked runtime checks used Node 26.10.0
and npm 12.2.0. Resolve versions again for a later project; keep the qualified
graph when reproducing this snapshot.

Actual controls pass SVG/JPEG-to-PNG dimensions, rejected non-images, all three
logo fallbacks, current SDK image/validation response parsing and CLI help.
Negative controls also reproduce short-key masking crashes and failed QA that
still saves an image, exits zero and prints success. Passing a negative control
means that the defect was observed. These responses were intercepted fixtures;
no actual provider model availability or generation quality was tested.

Do not adopt the old CLI unchanged after updating its dependencies. Repair and
verify its status, credential, response-schema, overwrite and network/resource
contracts, or use a qualified image tool already supplied by the environment.
Local control results do not establish efficacy of this guidance for an agent.
